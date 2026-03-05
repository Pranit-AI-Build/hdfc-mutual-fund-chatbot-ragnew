## Phase 2 – Extraction Spec for Groww HDFC Mutual Fund Pages

**Goal:** Extract key mutual fund details from a fixed list of Groww URLs into a **structured, searchable knowledge base** so the RAG chatbot can answer questions without live page fetches.

Initial URLs (HDFC schemes):

- `https://groww.in/mutual-funds/hdfc-banking-financial-services-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-nifty-next-50-index-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth`
- `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth`

This document defines **what to extract** and **how it maps** into the knowledge base schema (see `knowledge-base-format.md` in the same folder).

---

### 1. Target Record Structure (per URL)

Each fund page should produce **one logical record** with these top‑level fields:

- `source_url`
- `scheme_name`
- `nav`
- `nav_date` (if available)
- `min_sip_amount`
- `fund_size`
- `expense_ratio`
- `fund_managers` (array of names)
- `returns` (object: 1Y, 3Y, 5Y, since inception)
- `top_holdings` (array of { company, sector?, weight_percent })
- `holding_analysis` (text summary and/or structured breakdown)
- `exit_load`
- `tax_info`
- `description` (key descriptive text / overview)

These correspond closely to the user‑facing fields on each Groww fund page.

---

### 2. Fields to Extract – Detailed

For each URL, extract the following:

#### 2.1 Identification & Source

- **`source_url`**
  - **Type**: string
  - **Meaning**: The exact URL the data came from.
  - **Use**: Traceability, debugging, future refresh.

- **`scheme_name`**
  - **Type**: string
  - **Example**: `"HDFC Small Cap Fund Direct Growth"`
  - **Use**: Display name and entity resolution in the chatbot.

---

#### 2.2 NAV (Net Asset Value)

- **`nav`**
  - **Type**: number (float)
  - **Example**: `123.45`
  - **Parse from**: “NAV” section on the page (strip currency symbol; parse to numeric).

- **`nav_date`**
  - **Type**: string (ISO date if possible, e.g., `"2026-02-28"`)
  - **Parse from**: The “as on” date shown next to NAV, if present.

---

#### 2.3 Minimum SIP Amount

- **`min_sip_amount`**
  - **Type**: number (integer)
  - **Example**: `1000`
  - **Parse from**: “Minimum SIP” or similar label (strip `₹`, commas, and text like `/month`).

---

#### 2.4 Fund Size

- **`fund_size`**
  - **Type**: object
  - **Shape**:
    - `amount`: number (float)
    - `currency`: string (e.g., `"INR"`)
    - `unit`: string (e.g., `"Cr"`, `"Lakh"`, `"Crore"`)
  - **Example**:
    - `{ "amount": 3500.0, "currency": "INR", "unit": "Cr" }`
  - **Parse from**: “Fund Size” / “AUM” section, typically expressed like “₹3,500 Cr”.

---

#### 2.5 Expense Ratio

- **`expense_ratio`**
  - **Type**: number (float, representing percentage)
  - **Example**: `0.0125` for 1.25%
  - **Parse from**: “Expense Ratio” section; read `1.25%` and convert to decimal.

---

#### 2.6 Fund Managers

- **`fund_managers`**
  - **Type**: array of strings
  - **Example**:
    - `[ "Mr. X FundManager", "Ms. Y Co-Manager" ]`
  - **Parse from**: “Fund Manager” / “Fund Managers” section; split by comma or bullet list where applicable.

---

#### 2.7 Returns (1Y, 3Y, 5Y, Since Inception)

- **`returns`**
  - **Type**: object
  - **Shape**:
    - `one_year`: number or null (decimal for percent, e.g., `0.1234` for 12.34%)
    - `three_year`: number or null
    - `five_year`: number or null
    - `since_inception`: number or null
  - **Parse from**: Performance table on the page.
    - Extract fund’s own return row (not benchmark/category row).
    - Convert `%` strings to decimals.

Example:

```json
{
  "one_year": 0.1280,
  "three_year": 0.1850,
  "five_year": 0.2105,
  "since_inception": 0.1560
}
```

---

#### 2.8 Top Holdings (Companies & %)

- **`top_holdings`**
  - **Type**: array of objects
  - **Shape per holding**:
    - `company_name`: string
    - `sector`: string or null (if shown)
    - `weight_percent`: number (decimal, e.g., `0.074` for 7.4%)
  - **Parse from**: “Top Holdings” table or section:
    - Company column → `company_name`.
    - Sector column (if present) → `sector`.
    - % allocation column → `weight_percent`.

Example:

```json
[
  { "company_name": "HDFC Bank Ltd", "sector": "Financial", "weight_percent": 0.074 },
  { "company_name": "ICICI Bank Ltd", "sector": "Financial", "weight_percent": 0.062 }
]
```

---

#### 2.9 Holding Analysis of the Fund

- **`holding_analysis`**
  - **Type**: object
  - **Suggested shape**:
    - `by_sector`: array of { `sector`, `weight_percent` }
    - `by_market_cap`: array of { `bucket`, `weight_percent` } where bucket ∈ { `"Large Cap"`, `"Mid Cap"`, `"Small Cap"`, `"Others"` }
    - `raw_text`: string (optional free‑form holding commentary, if available)
  - **Parse from**:
    - “Sector Allocation”, “Market Cap Allocation” charts/tables.
    - Any descriptive text summarizing portfolio positioning.

Example:

```json
{
  "by_sector": [
    { "sector": "Financial Services", "weight_percent": 0.36 },
    { "sector": "Consumer Goods", "weight_percent": 0.18 }
  ],
  "by_market_cap": [
    { "bucket": "Large Cap", "weight_percent": 0.55 },
    { "bucket": "Mid Cap", "weight_percent": 0.30 },
    { "bucket": "Small Cap", "weight_percent": 0.15 }
  ],
  "raw_text": "The fund is overweight financials and mid-cap stocks compared to its benchmark."
}
```

If detailed charts are not easily parseable, you can choose to initially populate only `raw_text` with any available portfolio commentary from the page.

---

#### 2.10 Exit Load

- **`exit_load`**
  - **Type**: string
  - **Example**:
    - `"1% if redeemed within 1 year, 0% thereafter"`
  - **Parse from**: “Exit Load” / “Charges” / “Fees and Loads” section; retain descriptive wording.

---

#### 2.11 Tax Information / Implications

- **`tax_info`**
  - **Type**: string
  - **Content**:
    - Text summarizing tax treatment if present on the page (e.g., for ELSS or capital gains).
    - If not present, keep null and plan to enrich later from AMC/SEBI/AMFI.

---

#### 2.12 Other Key Descriptive Text

- **`description`**
  - **Type**: string
  - **Source**:
    - “About the fund”, “Fund Overview”, “Investment Objective”, “Key Highlights”, or similar sections.
  - **Use**:
    - Input to embeddings/vector store for semantic search.
    - High‑level explanation for users.

---

### 3. Extraction Output Format

See `knowledge-base-format.md` in this folder for:

- JSONL structure for each fund record.
- Example records for at least one HDFC fund.
- Conventions for decimals, dates, and null handling.

That file defines **how** these fields are stored so the RAG chatbot can query them efficiently.

