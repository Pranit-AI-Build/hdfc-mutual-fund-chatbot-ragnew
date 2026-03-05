## Knowledge Base Format – Fund Records for RAG

This file defines the **storage format** for the extracted data from the Groww HDFC fund URLs.  
Each fund page becomes **one JSON object** in a JSON Lines (`.jsonl`) file.

You can store them in, for example:

- `Phase2/data/funds.jsonl`

Each line = one fund record.

---

### 1. Top‑Level JSON Schema (Conceptual)

```json
{
  "source_url": "string",
  "scheme_name": "string",
  "nav": 0.0,
  "nav_date": "YYYY-MM-DD",
  "min_sip_amount": 0,
  "fund_size": {
    "amount": 0.0,
    "currency": "INR",
    "unit": "Cr"
  },
  "expense_ratio": 0.0,
  "fund_managers": ["string"],
  "returns": {
    "one_year": 0.0,
    "three_year": 0.0,
    "five_year": 0.0,
    "since_inception": 0.0
  },
  "top_holdings": [
    {
      "company_name": "string",
      "sector": "string",
      "weight_percent": 0.0
    }
  ],
  "holding_analysis": {
    "by_sector": [
      { "sector": "string", "weight_percent": 0.0 }
    ],
    "by_market_cap": [
      { "bucket": "string", "weight_percent": 0.0 }
    ],
    "raw_text": "string"
  },
  "exit_load": "string",
  "tax_info": "string",
  "description": "string"
}
```

Notes:

- Numeric percentages (returns and weights) are stored as **decimals** (e.g., `0.1234` for 12.34%).
- Any field that is unknown/unavailable should be set to `null` or omitted (decide one convention and stick to it; recommended: use `null`).

---

### 2. Example Record (Hypothetical Data)

```json
{
  "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
  "scheme_name": "HDFC Small Cap Fund Direct Growth",
  "nav": 123.45,
  "nav_date": "2026-02-28",
  "min_sip_amount": 1000,
  "fund_size": {
    "amount": 3500.0,
    "currency": "INR",
    "unit": "Cr"
  },
  "expense_ratio": 0.0125,
  "fund_managers": [
    "Mr. X Manager",
    "Ms. Y Co-Manager"
  ],
  "returns": {
    "one_year": 0.1280,
    "three_year": 0.1850,
    "five_year": 0.2105,
    "since_inception": 0.1560
  },
  "top_holdings": [
    { "company_name": "ABC Small Cap Ltd", "sector": "Industrials", "weight_percent": 0.074 },
    { "company_name": "XYZ Components Ltd", "sector": "Consumer Goods", "weight_percent": 0.062 }
  ],
  "holding_analysis": {
    "by_sector": [
      { "sector": "Industrials", "weight_percent": 0.30 },
      { "sector": "Consumer Goods", "weight_percent": 0.18 },
      { "sector": "Financial Services", "weight_percent": 0.15 }
    ],
    "by_market_cap": [
      { "bucket": "Small Cap", "weight_percent": 0.70 },
      { "bucket": "Mid Cap", "weight_percent": 0.20 },
      { "bucket": "Large Cap", "weight_percent": 0.10 }
    ],
    "raw_text": "The fund is predominantly invested in small-cap industrial and consumer companies."
  },
  "exit_load": "1% if redeemed within 1 year from the date of allotment, 0% thereafter.",
  "tax_info": "Equity-oriented scheme. Long-term capital gains (LTCG) tax as per prevailing equity taxation rules; ELSS schemes may offer tax deduction under Section 80C, subject to conditions.",
  "description": "HDFC Small Cap Fund is an open-ended equity scheme predominantly investing in small-cap stocks with the objective of generating long-term capital appreciation."
}
```

---

### 3. How the RAG Chatbot Uses This

- **Direct fact lookups**:
  - NAV, min SIP, fund size, expense ratio, fund managers, exit load.
- **Performance explanations**:
  - Values from `returns` with “as of” date from `nav_date` or a separate performance date if you add one later.
- **Portfolio/holding commentary**:
  - `top_holdings` and `holding_analysis` for “top holdings” and “sector/market-cap allocation” questions.
- **Tax and descriptive queries**:
  - `tax_info` and `description` for explanations and FAQs.

In later steps, you can:

- Load this JSONL file into:
  - A document/relational store (for structured Q&A).
  - A vector store (embedding `description`, `tax_info`, and any other long text) for semantic search.

---

### 4. Next Implementation Step (When Ready)

When you’re ready to implement extraction, you can:

1. Write a small script (e.g., Python + `requests` + `BeautifulSoup`) that:
   - Iterates over the 9 URLs.
   - Scrapes each page.
   - Parses the specific sections described in `extraction-spec.md`.
   - Produces records exactly following this JSON schema.
2. Append each record as one line in `Phase2/data/funds.jsonl`.

That script can live in `Phase2/` (for example `Phase2/extract_groww_hdfc.py`) and should strictly adhere to this schema so the RAG layer and later phases can use it without changes.

