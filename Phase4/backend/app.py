import os
import re
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNDS_PATH = os.path.join(BASE_DIR, "Phase2", "data", "funds.jsonl")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    fund_name: Optional[str]
    source_url: Optional[str]
    nav_date: Optional[str]


app = FastAPI(title="HDFC Mutual Fund Chatbot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_funds() -> List[Dict[str, Any]]:
    funds: List[Dict[str, Any]] = []
    if not os.path.exists(FUNDS_PATH):
        raise RuntimeError(f"Fund data file not found at: {FUNDS_PATH}")
    with open(FUNDS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            import json

            funds.append(json.loads(line))
    return funds


FUNDS_CACHE: Optional[List[Dict[str, Any]]] = None


def get_funds() -> List[Dict[str, Any]]:
    global FUNDS_CACHE
    if FUNDS_CACHE is None:
        FUNDS_CACHE = load_funds()
    return FUNDS_CACHE


PII_PATTERNS = [
    re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b"),  # 16-digit numbers (card-like)
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE),  # PAN-like
    re.compile(r"\b\d{12}\b"),  # Aadhaar-like
    re.compile(r"\b\d{10}\b"),  # phone-like
    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),  # email
]


def contains_pii(text: str) -> bool:
    for pat in PII_PATTERNS:
        if pat.search(text):
            return True
    return False


def find_best_fund(query: str) -> Optional[Dict[str, Any]]:
    query_lower = query.lower()
    best: Optional[Dict[str, Any]] = None
    best_score = 0
    for fund in get_funds():
        name = (fund.get("fund_name") or "").lower()
        if not name:
            continue
        if query_lower in name:
            score = len(query)
        else:
            # basic token overlap score
            score = len(set(query_lower.split()) & set(name.split()))
        if score > best_score:
            best_score = score
            best = fund
    return best


def build_context_for_fund(fund: Dict[str, Any]) -> str:
    parts = [
        f"Fund name: {fund.get('fund_name')}",
        f"NAV: {fund.get('nav')} (as of {fund.get('nav_date')})",
        f"Minimum SIP: {fund.get('minimum_sip')}",
        f"Fund size: {fund.get('fund_size')}",
        f"Expense ratio: {fund.get('expense_ratio')}",
        f"Risk level: {fund.get('risk_level')}",
        f"Exit load: {fund.get('exit_load')}",
    ]
    return "\n".join(str(p) for p in parts if p is not None)


def call_groq(prompt: str, context: str) -> str:
    if not GROQ_API_KEY:
        # In dev, avoid hard failure and return a deterministic stub.
        return (
            "I do not have live model access configured. "
            "Please set GROQ_API_KEY in the environment."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an HDFC Mutual Fund assistant. "
                    "You must answer ONLY using the structured context provided. "
                    "Do not use any external knowledge or live data. "
                    "Do NOT accept, store, or repeat personal identifiers such as "
                    "PAN, Aadhaar, account numbers, OTPs, phone numbers, or emails. "
                    "Do NOT compute or compare returns or performance; if asked for "
                    "detailed performance, direct the user to the official factsheet URL "
                    "contained in the context. "
                    "Keep answers under 3 sentences. "
                    "Do not provide investment advice or recommendations."
                ),
            },
            {
                "role": "user",
                "content": f"User question: {prompt}\n\nContext:\n{context}",
            },
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }
    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Groq API error: {resp.status_code} {resp.text}")
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Unexpected Groq response: {data}") from exc


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    if contains_pii(message):
        safe_text = (
            "I’m not allowed to process personal identifiers such as PAN, "
            "Aadhaar, account numbers, OTPs, emails, or phone numbers. "
            "Please ask a general question about our mutual funds instead."
        )
        return ChatResponse(answer=safe_text, fund_name=None, source_url=None, nav_date=None)

    fund = find_best_fund(message)
    if not fund:
        answer = (
            "I could not identify a specific HDFC fund from your question. "
            "Please include the full fund name from our scheme list."
        )
        return ChatResponse(answer=answer, fund_name=None, source_url=None, nav_date=None)

    # Enforce no performance calculations: if question focuses on returns/performance,
    # direct user to the official source instead of asking LLM to compute anything.
    if re.search(r"\b(return|performance|CAGR|XIRR)\b", message, re.IGNORECASE):
        source_url = fund.get("source_url")
        nav_date = fund.get("nav_date")
        fund_name = fund.get("fund_name")
        answer = (
            f"For {fund_name}, performance details are available in the official factsheet "
            f"and AMC disclosures. Please refer to the latest document on the source site."
        )
        footer = f" Last updated: {nav_date or 'N/A'} (Source: {source_url or 'N/A'})."
        return ChatResponse(
            answer=answer + footer,
            fund_name=fund_name,
            source_url=source_url,
            nav_date=nav_date,
        )

    context = build_context_for_fund(fund)
    llm_answer = call_groq(message, context)

    # Ensure answer is at most ~3 sentences (simple split).
    sentences = re.split(r"(?<=[.!?])\s+", llm_answer.strip())
    trimmed = " ".join(sentences[:3]).strip()

    source_url = fund.get("source_url")
    nav_date = fund.get("nav_date")
    footer = f" Last updated: {nav_date or 'N/A'} (Source: {source_url or 'N/A'})."

    return ChatResponse(
        answer=trimmed + footer,
        fund_name=fund.get("fund_name"),
        source_url=source_url,
        nav_date=nav_date,
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

