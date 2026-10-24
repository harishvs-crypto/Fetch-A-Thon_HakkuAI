# HakkuAI Architecture Specification

HakkuAI is an autonomous, AI-powered government welfare assistance agent built on Fetch.ai's `uagents` framework and the official Agent Communication Protocol (ACP) for Fetch-A-Thon 3.0.

HakkuAI assists vulnerable unorganized workers in India—specifically daily-wage construction laborers who experience workplace injuries and wage loss—in discovering verified welfare schemes, understanding statutory rights under Indian labor laws, and receiving personalized document checklists.

---

## 1. System Architecture Overview

```
                      +---------------------------------------+
                      |               ASI:One                 |
                      |     (Natural Language Discovery)      |
                      +-------------------+-------------------+
                                          |
                                          | Agent Chat Protocol (ACP v0.3.0)
                                          v
                      +---------------------------------------+
                      |       Fetch.ai Agentverse Gateway     |
                      |    (Almanac Registry / Mailbox Proxy) |
                      +-------------------+-------------------+
                                          |
                                          v
+-------------------------------------------------------------------------------+
|                             HakkuAI uAgent                                    |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  |                     ACP Message Dispatcher & Handlers                   |  |
|  |   - ChatMessage / ChatAcknowledgement Handler                           |  |
|  |   - Structured Welfare RPC Handler (WelfareAssessmentRequest)           |  |
|  +------------------------------------+------------------------------------+  |
|                                       |                                       |
|                                       v                                       |
|  +-------------------------------------------------------------------------+  |
|  |                    Conversational Engine & Session Manager              |  |
|  |   - Isolated Per-Sender User Sessions (Zero cross-worker leakage)       |  |
|  |   - Progressive Attribute Extraction (No rigid questionnaire barriers)  |  |
|  |   - Bilingual Processing (English + Tamil தமிழ்)                        |  |
|  |   - Privacy-Safe PII Stripping (No Aadhaar / Bank passwords recorded)   |  |
|  +----+------------------+-------------------+------------------+----------+  |
|       |                  |                   |                  |             |
|       v                  v                   v                  v             |
|  +----------+    +---------------+    +--------------+    +----------------+  |
|  |  Injury  |    | Deterministic |    | Document     |    | Source         |  |
|  | Guidance |    | Eligibility   |    | Checklist    |    | Integrity      |  |
|  | Workflow |    | Engine        |    | Generator    |    | Manager        |  |
|  | (112/108)|    | (Pure Python) |    | (Fallback)   |    | (.gov.in check)|  |
|  +----+-----+    +-------+-------+    +------+-------+    +-------+--------+  |
|       |                  |                   |                    |           |
|       +------------------+-------------------+--------------------+           |
|                                       |                                       |
|                                       v                                       |
|  +-------------------------------------------------------------------------+  |
|  |                 Verified Scheme Knowledge Base (Local JSON)              |  |
|  |   - Tamil Nadu BOCW Welfare Board Accident Relief Scheme                |  |
|  |   - Employees' Compensation Act, 1923 (Statutory Employer Liability)    |  |
|  |   - Ayushman Bharat - PMJAY (Secondary/Tertiary Hospital Care)          |  |
|  |   - Pradhan Mantri Suraksha Bima Yojana (PMSBY Accident Insurance)      |  |
|  |   - e-Shram National Unorganised Workers Database                       |  |
|  |   - Karnataka BOCW Welfare Board Accident Benefit Scheme                |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

### A. Honest Uncertainty vs. Hallucination Prevention
- The agent **never promises** benefits or issues official government rulings.
- Outcomes are explicitly labeled as:
  1. `Potentially eligible`: Meets documented preliminary conditions; subject to official departmental sanction.
  2. `More information needed`: Missing critical data points (e.g., board enrollment number, accident incident report).
  3. `Likely not eligible`: Clearly does not satisfy defined statutory criteria (e.g., non-construction workers attempting to claim BOCW funds).
  4. `Unverified / Incomplete data`: Triggered when a worker resides in a state whose state-specific BOCW rules are not yet indexed in HakkuAI's local verified registry. Rather than fabricating scheme amounts, HakkuAI explicitly discloses data limits and directs the worker to the local State Labour Commissioner.

### B. Deterministic Eligibility Engine (`eligibility.py`)
- Business rules are written as pure, testable Python functions completely decoupled from natural language generation.
- Strict geographic matching ensures a worker in Tamil Nadu is never served Karnataka-specific state schemes.
- Universal statutory remedies (such as the Central *Employees' Compensation Act, 1923*) are matched independently of state board registration.

### C. Privacy by Design & PII Sanitization (`logging_config.py`)
- The agent explicitly forbids collecting sensitive credentials (Aadhaar numbers, bank passwords, ATM PINs, OTPs).
- The internal logging pipeline features an active regex filter that redacts accidental occurrences of Aadhaar numbers (`\d{4}\s\d{4}\s\d{4}`), phone numbers, and bank account numbers before writing to stdout.

### D. Emergency Safety Prioritization (`injury_workflow.py`)
- If the user communicates trauma indicators (unconsciousness, uncontrolled hemorrhage, crush injury, respiratory distress), HakkuAI immediately triggers an **Emergency Banner** prioritizing immediate medical care:
  - **National Emergency Helpline**: `112`
  - **Ambulance Service**: `108`
- Procedural paperwork and welfare claims are explicitly postponed until patient stabilization.

### E. Session Isolation (`conversation.py`)
- Each incoming agent address or user connection receives an isolated `UserSession`.
- Conversational turns, medical attributes, and language preferences are stored strictly in-memory per sender key, preventing cross-worker data contamination.

---

## 3. Technology Stack & Interface Boundaries

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Agent Framework** | `uagents` | `>=0.26.1` | Fetch.ai autonomous agent foundation |
| **Protocol Core** | `uagents-core` | `>=0.4.12` | Official Agent Chat Protocol (ACP v0.3.0) & Model base |
| **Validation** | `pydantic` | `>=2.0.0` | Strict data validation & schema contracts |
| **Language Support** | Python 3.11 | `3.11.9` | High performance runtime |
| **Configuration** | `python-dotenv` | `>=1.0.0` | Zero-hardcoding environment management |
| **Test Framework** | `pytest` + `pytest-asyncio` | `>=8.0` | Comprehensive unit, protocol & E2E suite |
| **Health API** | `fastapi` + `uvicorn` | `>=0.100` | Optional auxiliary healthcheck daemon |
