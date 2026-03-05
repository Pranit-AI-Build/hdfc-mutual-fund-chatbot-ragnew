# HDFC Mutual Fund FAQ Chatbot

A Retrieval-Augmented Generation (RAG) based FAQ assistant for HDFC Mutual Fund schemes. This chatbot answers factual questions about HDFC mutual funds including NAV, expense ratio, exit load, minimum SIP, returns, and more.

## Features

- **Factual Q&A**: Answers questions about HDFC Mutual Fund schemes only
- **Data-driven**: Uses stored fund data from public sources (Groww)
- **Compliance-first**: 
  - No investment advice
  - No personal data handling (PAN, Aadhaar, etc.)
  - Strict scope enforcement (HDFC Mutual Fund only)
- **Source Attribution**: All answers include source URLs

## Architecture

```
User Query → Fund Matching → Context Building → LLM (Groq) → Answer with Source
```

### Components

1. **Backend** (`Phase4/backend/app.py`)
   - FastAPI server
   - Fund matching algorithm
   - Groq LLM integration
   - PII and scope validation

2. **Frontend** (`Phase4/frontend/`)
   - HTML/CSS/JS chat interface
   - Responsive design
   - Real-time messaging

3. **Data** (`Phase2/data/funds.jsonl`)
   - HDFC mutual fund data
   - NAV, returns, expense ratio, exit load, etc.

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
cd "Mutual Funds - Cursor"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your GROQ_API_KEY
```

### Running the Application

1. Start the backend server:
```bash
python -m uvicorn Phase4.backend.app:app --host 127.0.0.1 --port 5000 --reload
```

2. Start the frontend server (in a new terminal):
```bash
cd Phase4/frontend
python -m http.server 3000
```

3. Open your browser and navigate to:
```
http://localhost:3000
```

## Usage

Ask questions like:
- "What is the NAV of HDFC Small Cap Fund?"
- "What is the exit load for HDFC Flexi Cap Fund?"
- "What are the returns for HDFC Banking & Financial Services Fund?"

## Compliance Rules

The chatbot strictly enforces:

✅ **Allowed**:
- Factual questions about HDFC Mutual Fund schemes
- NAV, expense ratio, exit load, minimum SIP
- Returns (6 months, 1 year, 3 years, 5 years)
- Lock-in periods (ELSS)
- Benchmark and riskometer

❌ **Not Allowed**:
- Investment advice or recommendations
- Comparisons with other AMCs
- Personal data requests (PAN, Aadhaar, bank details, OTP, email, phone)
- Non-mutual fund topics (stocks, crypto, FD, PPF, etc.)

**Out-of-scope response**: "I can only give answers related to HDFC Mutual Fund schemes."

## Project Structure

```
.
├── Phase2/
│   └── data/
│       └── funds.jsonl          # Fund data
├── Phase4/
│   ├── backend/
│   │   └── app.py               # FastAPI backend
│   └── frontend/
│       ├── index.html           # Chat UI
│       ├── main.js              # Frontend logic
│       └── styles.css           # Styling
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Data Sources

Fund data is sourced from:
- Groww mutual fund pages


## Technology Stack

- **Backend**: Python, FastAPI, Groq API
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **LLM**: Llama 3.3 70B (via Groq)

## License

This project is for educational purposes.

## Scope

### AMC Coverage
- **Only HDFC Mutual Fund** schemes are supported
- 9 schemes currently available:
  - HDFC Banking & Financial Services Fund Direct Growth
  - HDFC Small Cap Fund Direct Growth
  - HDFC Flexi Cap Direct Plan Growth
  - HDFC NIFTY Next 50 Index Fund Direct Growth
  - HDFC Large and Mid Cap Fund Direct Growth
  - HDFC ELSS Tax Saver Fund Direct Plan Growth
  - HDFC Large Cap Fund Direct Growth
  - HDFC Defence Fund Direct Growth
  - HDFC Mid Cap Fund Direct Growth

### Allowed Topics
- NAV (Net Asset Value)
- Expense Ratio
- Exit Load
- Minimum SIP amount
- Lock-in period (ELSS)
- Riskometer
- Scheme rules

## Known Limits

- **No returns computation, comparison, or analysis** - The chatbot does not calculate, compare, or analyze returns
- **No investment advice** - Cannot provide recommendations on which fund to buy/sell
- **No other AMCs** - Questions about SBI, ICICI, Axis, or other mutual fund companies are not supported
- **No personal data handling** - Cannot process PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers
- **No non-MF topics** - Stocks, crypto, fixed deposits, PPF, NPS, real estate, gold are out of scope
- **Fund name matching** - Requires specific fund names; generic queries may not match correctly
- **Data freshness** - NAV and returns data is from stored snapshots, not real-time

## Disclaimer

This chatbot provides factual information only and does not constitute investment advice. Always consult a financial advisor before making investment decisions.
