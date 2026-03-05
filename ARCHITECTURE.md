## Mutual Fund RAG Chatbot – Phase‑wise Architecture

### 1. Objectives & Scope

- **Business goal**: Provide an informational chatbot for a mutual fund AMC that can answer scheme‑related questions (facts, performance, risk, comparisons, FAQs) using only approved public data sources.
- **Initial scope**: HDFC mutual fund schemes corresponding to the following Groww‑style pages (extensible to more schemes and AMCs later):
  - `hdfc-banking-financial-services-fund-direct-growth`
  - `hdfc-small-cap-fund-direct-growth`
  - `hdfc-equity-fund-direct-growth`
  - `hdfc-nifty-next-50-index-fund-direct-growth`
  - `hdfc-large-and-mid-cap-fund-direct-growth`
  - `hdfc-elss-tax-saver-fund-direct-plan-growth`
  - `hdfc-large-cap-fund-direct-growth`
  - `hdfc-defence-fund-direct-growth`
  - `hdfc-mid-cap-fund-direct-growth`
- **Out of scope (Phase 1)**: Production‑grade deployment, UI, operations. Phase 1 focuses on architecture and design only.

---

### 2. High‑Level System Overview

The solution is a **Retrieval‑Augmented Generation (RAG)** system with three main logical layers:

1. **Data & Ingestion Layer**
   - Fetches and parses mutual fund scheme data from public sources (AMC website, PDFs, distributor pages such as the above Groww URLs).
   - Normalizes data into structured entities (schemes, performance, portfolios) and text documents (objectives, strategy, risk factors, FAQs).
2. **Knowledge & Retrieval Layer**
   - Stores structured data in a database and unstructured text in a vector store with embeddings and rich metadata.
   - Provides retrieval APIs for both semantic (vector) search and deterministic fact lookup (DB queries).
3. **RAG & Application Layer**
   - Interprets user questions, retrieves relevant facts and documents, and uses an LLM to generate compliant, cited, non‑advisory responses.
   - Exposes APIs for future integration into web/mobile/chat channels.

In Phase 1, only the **logical architecture** and **data/interaction design** are produced; implementation is deferred to later phases.

---

### 3. Data Model & Sources

#### 3.1 Core Entities

- **Scheme**
  - Identifiers: `scheme_id`, `scheme_name`, `plan_type` (Regular/Direct), `option` (Growth/IDC&W), ISIN(s), AMFI code.
  - Classification: AMC name, SEBI category (e.g., Small Cap, Large & Mid Cap, ELSS), benchmark index, risk‑o‑meter label.
  - Attributes: launch date, AUM, minimum SIP and lump sum, expense ratio, exit load, lock‑in (for ELSS), fund manager(s).
- **SchemePerformance**
  - Attributes: return values for standard periods (1M, 3M, 6M, 1Y, 3Y, 5Y, since inception), CAGR, benchmark returns, category returns.
  - Metadata: `as_of_date`, source (factsheet, distributor page, etc.).
- **SchemePortfolio**
  - Holdings: security name, sector, asset type (equity, debt, cash), weight %, market‑cap bucket (for equity funds).
  - Aggregations: sector allocation, market‑cap allocation, top holdings lists.
- **SchemeDocuments**
  - Long‑form text: investment objective, strategy, risk factors, key features, commentary, notes from SID/KIM/factsheets and curated pages.
  - Metadata: `scheme_id`, `doc_type` (factsheet, SID, KIM, FAQ, commentary), `section`, `as_of_date`.
- **FAQEntry**
  - Frequently asked questions and answers related to schemes and general mutual fund topics (tax treatment, SIP operational rules, lock‑in rules).
  - Source: AMC website, SEBI/AMFI, curated internal content.

#### 3.2 Data Sources

- **Primary sources**
  - Official AMC website pages (scheme microsites, factsheets, SID, KIM PDFs).
  - Public distributor pages such as the provided Groww URLs for each HDFC scheme.
- **Optional secondary sources**
  - AMFI and other industry‑standard feeds for cross‑validation of basic attributes (AUM, classification, codes).

---

### 4. Phase‑wise Architecture

#### Phase 1 – Discovery & Architecture (current phase)

**Objective:** Finalize requirements, data model, and overall RAG system design. No development or deployment.

- **Activities**
  - Requirements capture:
    - Enumerate user questions across: scheme facts, performance, risk, comparisons, and operational FAQs.
    - Define strict boundaries to avoid personalized investment advice.
  - Data assessment:
    - Analyze structure of representative pages (e.g., HDFC Small Cap Fund Direct Growth) and PDF documents.
    - Identify which attributes and text sections are reliably available and how often they change.
  - Data model design:
    - ER diagram for `Scheme`, `SchemePerformance`, `SchemePortfolio`, `SchemeDocuments`, `FAQEntry`.
    - Naming conventions and normalization rules for scheme names and categories.
  - System architecture:
    - Logical diagrams for ingestion, storage, retrieval, and RAG layers (see sections below).
    - Interface contracts between layers (input/output fields and responsibilities).
- **Deliverables**
  - Architecture document (this file) and complementary diagrams.
  - Data dictionary for core entities and fields.
  - High‑level sequence flows for main query types.

#### Phase 2 – Data Ingestion & Knowledge Base

**Objective:** Implement an offline data pipeline to build and maintain the knowledge base used by the chatbot.

- **Ingestion & ETL Layer**
  - **Fetchers**
    - Scheduled jobs to download HTML from configured scheme URLs (starting with the nine HDFC schemes listed above).
    - PDF downloaders for factsheets, SID, and KIM from the AMC website.
  - **Parsers**
    - HTML parsers to extract:
      - Fund overview (category, benchmark, risk‑o‑meter, AUM, expense, min investment).
      - Performance tables (periodic returns) and benchmark/category comparison.
      - Holdings/sector allocation tables.
      - Textual fields (objectives, strategy, risk section, about the fund).
    - PDF parsers for long‑form textual sections (especially for SID/KIM risk factors and detailed strategy).
  - **Normalization**
    - Map external scheme names to canonical `scheme_id`.
    - Convert numeric and date formats, standardize category labels.
  - **Validation**
    - Schema checks (required fields present, valid types and ranges).
    - Basic cross‑checks (e.g., risk‑o‑meter vs category; AUM non‑negative; dates reasonable).

- **Storage & Versioning**
  - **Raw layer**
    - Object storage for original HTML and PDFs (immutable, fully traceable).
  - **Curated structured store**
    - Relational or document database with normalized tables/collections for:
      - `schemes`, `scheme_performance`, `scheme_portfolio`, `scheme_documents`, `faqs`.
    - Versioned records with `effective_from` / `effective_to` and `as_of_date` for performance and disclosures.

- **Vectorization**
  - Chunk `scheme_documents` and curated FAQ answers into overlapping text segments with metadata:
    - `scheme_id`, `scheme_name`, `doc_type`, `section`, `as_of_date`, `risk_category`.
  - Use an embedding model to encode chunks and store them in a vector database.
  - Indexing strategy:
    - Primary filters: `scheme_id`, `doc_type`.
    - Secondary filters: SEBI category, risk‑o‑meter level, `as_of_date` ranges.

#### Phase 3 – RAG Question‑Answer Engine (Sandbox, using Groq)

**Objective:** Build the core reasoning engine that will power the chatbot, operating initially in a non‑production sandbox, using **Groq** as the LLM provider and enforcing strict data‑source and safety constraints.

- **LLM Provider (Groq)**
  - Use Groq’s Chat Completions API (`https://api.groq.com/openai/v1/chat/completions`) with a suitable model such as `llama-3.3-70b-versatile`.
  - The Groq API key is stored securely (e.g., environment variable like `GROQ_API_KEY`), never hard‑coded in the repo.

- **Intent & Entity Layer**
  - Classify question types:
    - `scheme_fact`, `risk_explanation`, `operational_FAQ`, `out_of_scope` (performance comparisons are treated as constrained facts, not new calculations).
  - Perform entity recognition:
    - Extract and normalize scheme names from user queries and map them to stored fund records (e.g., from `Phase2/data/funds.jsonl`).
    - Resolve ambiguities (e.g., multiple similar schemes) through clarification prompts if needed.

- **Retrieval Layer (Stored Data Only)**
  - **Structured retrieval (no live web fetch)**
    - For numeric and categorical facts (NAV, minimum SIP, fund size, expense ratios, exit loads, risk label, etc.), read from the curated store/JSONL and later the structured DB.
    - Do not compute or update performance numbers dynamically; use only what is already stored from approved public sources.
  - **Semantic retrieval (vector store, optional in sandbox)**
    - For explanatory questions (investment objective, strategy, generic risk/tax explanations), perform semantic search over documents and FAQs derived only from allowed public sources (AMC, regulator, approved aggregators).

- **Safety & Compliance Guardrails**
  - **Source restrictions**
    - Only use information that has been ingested from **approved public sources** (AMC websites, official documents, and curated distributor pages) and stored in the knowledge base.
    - No screenshots of internal back‑ends; no arbitrary third‑party blogs as sources.
  - **PII controls**
    - Pre‑LLM filter to detect and block PAN, Aadhaar, account numbers, OTPs, emails, phone numbers; respond with a safe message and do not log/store such content.
  - **Performance constraints**
    - The LLM is instructed not to compute or project returns, and not to compare performance numerically; instead, if users ask for detailed performance, it should direct them to the latest official factsheet/AMC page stored in metadata.

- **RAG Orchestration & Answer Generation**
  - Prepare a constrained prompt for Groq that:
    - Includes only retrieved fields and snippets from the stored data.
    - Explicitly states:
      - “You must not answer using external knowledge; only use the context provided.”
      - “Do not accept, store, or repeat any personal identifiers (PAN, Aadhaar, account numbers, OTPs, phone numbers, or emails).”
      - “Do not calculate or compare returns; if asked, refer to the stored factsheet URL instead.”
      - “Keep the answer under 3 sentences.”
      - “Always end with a line like: `Last updated: <DATE> (Source: <URL>)` based on the stored `nav_date` and source URL/metadata.”
  - The application code:
    - Assembles a compact JSON context for the LLM (selected fund record and any relevant descriptive snippets).
    - Calls Groq’s chat API with a system prompt encoding the constraints and a user prompt containing the original question plus the retrieved context.

- **Response Post‑processing**
  - Validate that the Groq response:
    - Has no obvious PII echoes from the input.
    - Mentions at most 3 sentences (or truncate safely if longer).
    - Includes the “Last updated: … (Source: …)” footer.

- **Evaluation**
  - Offline test harness with:
    - A curated set of user questions per scheme (NAV, minimum SIP, exit load, tax basics, generic risk explanations).
    - Checks that:
      - All answers are grounded in stored data.
      - No performance calculations or recommendations are made.
      - The 3‑sentence and “Last updated” rules are consistently followed.

#### Phase 4 – Frontend & Backend Chat Application

**Objective:** Design and implement the user‑facing chat application (frontend) and the orchestration backend that connects channels to the RAG engine.

- **Backend (Chat Orchestrator)**
  - Responsibilities:
    - Expose a **chat API layer** that fronts the RAG engine and hides complexity from clients.
    - Manage sessions, conversation history, and user context.
    - Apply channel‑specific policies (e.g., max message size, throttling).
  - Core endpoints:
    - `POST /chat/session` – create a new chat session (returns `session_id` and configuration such as language, disclaimer style).
    - `POST /chat/message` – send a user message for a specific `session_id` and return the bot’s response (and optional citations).
    - `GET /chat/history/{session_id}` – retrieve conversation history (for internal audit tools or RM consoles).
  - Integration with RAG engine:
    - For each message, call the RAG engine with:
      - User question and conversation context.
      - Optional user/channel metadata (e.g., language, segment, internal/external).
    - Receive a structured response with:
      - Answer text, citations, raw data used, and model metadata.
  - Observability:
    - Structured logs per interaction (session id, timestamps, model version, data snapshot id).
    - Application metrics (latency, errors, timeouts, token usage).

- **Frontend (Web / Mobile / Internal Console)**
  - Common UX principles:
    - Clear indication that this is an **informational mutual fund assistant**, not a financial advisor.
    - Prominent display of disclaimers (e.g., near the input box or in a header).
    - Support for copyable responses and citation viewing (e.g., “View source” link to factsheet section).
  - Web client (public AMC site):
    - Embeddable chat widget (floating button or sidebar) that:
      - On load, calls `POST /chat/session` to establish a session.
      - Sends user messages via `POST /chat/message` and renders streaming or full responses.
      - Displays message metadata (e.g., “Data as of <date>”) if available.
  - Mobile client:
    - Native or hybrid UI calling the same chat backend APIs.
    - Offline‑safe behavior (e.g., error states when network is poor).
  - Internal RM/agent console:
    - Extended view with:
      - Side panel showing retrieved sources, structured scheme data, and confidence indicators.
      - Ability for human agents to override or augment responses before sending to clients (if required).

- **Security & Compliance**
  - Authentication and authorization for internal tools (e.g., RM console).
  - Optional lightweight or no authentication for public web widget, with rate limiting and abuse protection.
  - Strict separation between:
    - Anonymous public interactions (no PII stored unless explicitly required and designed).
    - Authenticated internal/external user sessions (if introduced later with full regulatory and privacy review).

#### Phase 5 – APIs, Channels & Deployment

**Objective:** Expose the RAG engine and chat backend as secure, scalable services and integrate with multiple channels (web, mobile, internal tools).

- **Service Layer**
  - REST/gRPC APIs, for example:
    - `POST /chat` / `POST /chat/message` – multi‑turn conversational endpoint with session context.
    - `POST /ask` – single‑turn Q&A for system‑to‑system integrations.
  - Session management and conversation history storage.
  - Authentication and rate‑limiting mechanisms.

- **Channel Integrations**
  - Web widget embedded in AMC’s public site (using the frontend defined in Phase 4).
  - Mobile app SDK or API integration.
  - Internal RM/agent console with additional internal‑only insights (if required).

- **Deployment Architecture**
  - Environments: dev, UAT, prod.
  - Components:
    - Stateless API servers (RAG orchestrator and chat backend).
    - Vector database cluster.
    - Structured database with read replicas.
    - Batch ETL/ingestion workers.
  - Cross‑cutting:
    - Monitoring (metrics, logs, traces).
    - Centralized configuration and secrets management.

#### Phase 6 – Monitoring, Governance & Continuous Improvement

**Objective:** Ensure ongoing quality, compliance, and evolution of the chatbot.

- **Monitoring & Analytics**
  - Track: query volume, top intents, unanswered questions, fallback rates, latency, and model usage.
  - Dashboards for business and technical stakeholders.

- **Human‑in‑the‑loop Review**
  - Periodic review of conversation samples for accuracy and compliance.
  - Feedback loop to update FAQs, prompts, and training data for embeddings.

- **Data & Model Refresh**
  - Scheduled ETL runs:
    - Daily/weekly for NAV and performance updates.
    - Monthly or on‑change for factsheets and SID/KIM updates.
  - Controlled rollout of new embedding models or LLM versions, with A/B testing and offline evaluation before production.

- **Compliance & Risk Controls**
  - Standard responses and disclaimers for out‑of‑scope or advisory questions.
  - Clear logging/audit trails for responses (question, context, answer, model version, data snapshot).

---

### 5. Future Extensions

- Onboarding additional AMCs and schemes by:
  - Adding new source adapters for their websites and documents.
  - Reusing the existing ETL, storage, and RAG layers.
- Introducing personalization features in later phases (e.g., risk profiling, portfolio suitability checks) with strict consent, PII protection, and regulatory review.

