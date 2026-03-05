import os
import re
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    query_lower = query.lower().strip()
    best: Optional[Dict[str, Any]] = None
    best_score = -1
    
    # Define stop words that shouldn't contribute to matching
    stop_words = {'hdfc', 'fund', 'direct', 'growth', 'mutual', 'the', 'of', 'a', 'an', 'give', 'me', 'nav', 'what', 'is', 'get', 'tell', 'about'}
    
    # Extract meaningful keywords from query
    query_keywords = [w for w in query_lower.split() if w not in stop_words]
    
    for fund in get_funds():
        name = (fund.get("fund_name") or "").lower()
        if not name:
            continue
        
        # Remove stop words from fund name for comparison
        name_words = [w for w in name.split() if w not in stop_words]
        name_clean = " ".join(name_words)
        
        score = 0
        
        # Check for exact consecutive phrase matches
        query_clean = " ".join(query_keywords)
        if query_clean in name_clean:
            # Exact phrase match - highest score
            score = 1000 + len(query_clean) * 10
        else:
            # Check for keyword matches in order
            match_count = 0
            last_match_idx = -1
            
            for kw in query_keywords:
                try:
                    idx = name_words.index(kw, last_match_idx + 1)
                    if last_match_idx == -1 or idx == last_match_idx + 1:
                        # Consecutive match
                        match_count += 2
                    else:
                        # Non-consecutive match
                        match_count += 1
                    last_match_idx = idx
                except ValueError:
                    pass
            
            score = match_count * 10
        
        # Penalize if fund name has extra keywords not in query
        extra_words = len(set(name_words) - set(query_keywords))
        score -= extra_words * 5
        
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
    
    # Add returns data if available
    returns = fund.get('returns', {})
    if returns:
        returns_parts = []
        if returns.get('6_months'):
            returns_parts.append(f"6 months: {returns['6_months']}")
        if returns.get('1_year'):
            returns_parts.append(f"1 year: {returns['1_year']}")
        if returns.get('3_year'):
            returns_parts.append(f"3 years: {returns['3_year']}")
        if returns.get('5_year'):
            returns_parts.append(f"5 years: {returns['5_year']}")
        if returns_parts:
            parts.append("Returns: " + ", ".join(returns_parts))
    
    return "\n".join(str(p) for p in parts if p is not None)


def is_out_of_scope(message: str) -> bool:
    """Check if question is outside HDFC Mutual Fund scope."""
    message_lower = message.lower()
    
    # Check for sensitive/PII keywords
    sensitive_keywords = ['otp', 'password', 'pin', 'login', 'sign in', 'my account', 'portfolio']
    for kw in sensitive_keywords:
        if kw in message_lower:
            return True
    
    # Check for other AMCs
    other_amcs = ['sbi', 'icici', 'axis', 'kotak', 'nippon', 'uti', 'dsp', 'franklin', 'tata', 'canara']
    for amc in other_amcs:
        if amc in message_lower:
            return True
    
    # Check for non-mutual fund topics
    non_mf_topics = ['stock', 'share', 'crypto', 'bitcoin', 'fixed deposit', 'fd', 'ppf', 'nps', 'real estate', 'gold']
    for topic in non_mf_topics:
        if topic in message_lower:
            return True
    
    # Check if message contains any fund-related keywords
    fund_keywords = ['nav', 'expense', 'exit load', 'sip', 'lock-in', 'benchmark', 'riskometer', 'fund', 'scheme', 'hdfc']
    has_fund_keyword = any(kw in message_lower for kw in fund_keywords)
    
    # If no fund keywords, it's out of scope
    if not has_fund_keyword:
        return True
    
    return False


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
                    "You are a strict FAQ assistant for HDFC Mutual Fund. "
                    "You can ONLY answer factual questions about HDFC Mutual Fund schemes, such as: "
                    "NAV, Expense Ratio, Exit Load, Minimum SIP, Lock-in period, Benchmark, Riskometer, "
                    "How to download statements, Rules. "
                    "If the user asks anything outside these topics, reply exactly with: "
                    "I can only give answers related to HDFC Mutual Fund schemes. "
                    "If the user asks for or provides personal or sensitive information, including: "
                    "PAN, Aadhaar, Account numbers, OTPs, Emails, Phone numbers, "
                    "reply exactly with: "
                    "I can only give answers related to HDFC Mutual Fund schemes. "
                    "Do NOT compute, compare, or analyze returns. "
                    "If asked to do so, reply exactly with: "
                    "I can only give answers related to HDFC Mutual Fund schemes. "
                    "Keep answers short, factual, and limited to scheme information only. "
                    "You must answer ONLY using the structured context provided. "
                    "Do not use any external knowledge or live data. "
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

    # Check for PII
    if contains_pii(message):
        return ChatResponse(
            answer="I can only give answers related to HDFC Mutual Fund schemes.",
            fund_name=None,
            source_url=None,
            nav_date=None
        )

    # Check for out-of-scope questions
    if is_out_of_scope(message):
        return ChatResponse(
            answer="I can only give answers related to HDFC Mutual Fund schemes.",
            fund_name=None,
            source_url=None,
            nav_date=None
        )

    fund = find_best_fund(message)
    if not fund:
        # Check if it's a general question about statements or rules
        message_lower = message.lower()
        if 'statement' in message_lower or 'download' in message_lower:
            return ChatResponse(
                answer="You can download statements from the HDFC Mutual Fund website by logging into your account and navigating to the 'Statements' section.",
                fund_name=None,
                source_url="https://www.hdfcfund.com",
                nav_date=None
            )
        # Otherwise, it's out of scope
        return ChatResponse(
            answer="I can only give answers related to HDFC Mutual Fund schemes.",
            fund_name=None,
            source_url=None,
            nav_date=None
        )

    context = build_context_for_fund(fund)
    llm_answer = call_groq(message, context)

    # Ensure answer is at most ~3 sentences (simple split).
    sentences = re.split(r"(?<=[.!?])\s+", llm_answer.strip())
    trimmed = " ".join(sentences[:3]).strip()

    source_url = fund.get("source_url")
    nav_date = fund.get("nav_date")
    
    # Return answer without source - frontend will add it
    return ChatResponse(
        answer=trimmed,
        fund_name=fund.get("fund_name"),
        source_url=source_url,
        nav_date=nav_date,
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# Vercel serverless handler
# The app variable is already defined above for FastAPI

