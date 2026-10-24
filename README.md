# HakkuAI — AI Government Welfare Assistance Agent for Indian Workers

[![Fetch-A-Thon 3.0](https://img.shields.io/badge/Fetch--A--Thon-3.0%20Submission-blueviolet.svg)](https://fetch.ai)
[![Fetch.ai uAgents](https://img.shields.io/badge/Fetch.ai-uAgents%20v0.26.1-blue.svg)](https://github.com/fetchai/uAgents)
[![ACP Compliant](https://img.shields.io/badge/Protocol-AgentChatProtocol%20v0.3.0-success.svg)](https://uagents.fetch.ai)
[![Python 3.11](https://img.shields.io/badge/python-3.11-brightgreen.svg)](https://python.org)
[![Tests Passing](https://img.shields.io/badge/pytest-28%20passed%20%7C%20100%25-brightgreen.svg)](tests/)

> **HakkuAI** is an autonomous AI-powered government welfare assistance agent for Indian workers, initially specialized for daily-wage construction laborers who experience workplace injuries and lose their income. Built for **Fetch-A-Thon 3.0**.

---

## 1. Problem Statement & Mission

In India, over **450 million workers** make up the unorganized workforce. Daily-wage construction workers face hazardous work environments with frequent accidents, falls, and injuries. When injured:
- Workers lose daily wages and face catastrophic medical expenses.
- Workers and their families do not know about statutory welfare schemes or compensation rights.
- Employers and contractors frequently fail to register workers with state welfare boards or deny liability.
- Workers cannot navigate complex government websites or bureaucratic paperwork.

**HakkuAI solves this through a compassionate, progressive, bilingual AI agent.** Through a simple conversation in English or Tamil (தமிழ்), HakkuAI:
1. Prioritizes emergency medical care (**National Emergency 112 / Ambulance 108**) for acute trauma.
2. Discovers verified central and state-specific welfare benefits (such as BOCW Welfare Board Accident Relief and the Employees' Compensation Act 1923).
3. Evaluates eligibility deterministically with **honest uncertainty**—never promising government decisions or hallucinating benefit amounts.
4. Generates a personalized document checklist with actionable alternative evidence when documents are missing.
5. Directs workers to official government offices and validated government portals (`.gov.in`, `.nic.in`).
6. Guides workers on what to do when their employer never registered them or refuses to cooperate.

---

## 2. Core Capabilities

- **Progressive Conversational Intake**: Collects state, occupation, injury severity, registration status, and available documents gradually without rigid, bureaucratic forms.
- **Bilingual English & Tamil (தமிழ்) Support**: Empathetic, simple language explanations that avoid complicated legal jargon.
- **Deterministic Python Eligibility Engine**: Pure, testable rule evaluators separating factual matching from language generation.
- **Emergency Safety Prioritization**: Immediately detects life-threatening trauma and directs callers to **112 / 108** before any paperwork discussion.
- **Honest Uncertainty & Hallucination Prevention**: Explicitly labels outcomes as *Potentially eligible*, *More information needed*, *Likely not eligible*, or *Unverified data*. Never guesses or invents welfare figures for unindexed states.
- **Evidence Preservation & Unregistered Worker Guide**: Advises workers on how to prove on-duty injuries via muster rolls, co-worker affidavits, and how to invoke statutory rights under the *Employees' Compensation Act, 1923*.
- **Official Source Verification**: Tracks verification dates and validates official government domain authenticity (`.gov.in`, `.nic.in`).
- **Privacy by Design**: Masking filter prevents accidental logging of Aadhaar numbers, phone numbers, or bank account numbers.

---

## 3. Technology Stack

- **Core Framework**: `uagents` (v0.26.1)
- **Protocol Core**: `uagents-core` (v0.4.12) implementing official **Agent Chat Protocol (ACP v0.3.0)**
- **Runtime**: Python 3.11
- **Data Validation**: Pydantic v2
- **Testing**: `pytest` and `pytest-asyncio`
- **Knowledge Base**: Structured verified local JSON registry (`data/schemes.json`)
- **Auxiliary API**: FastAPI + Uvicorn (lightweight healthcheck endpoint)

---

## 4. Repository Structure

```
hakkuai/
  ├── README.md                      # Comprehensive project documentation
  ├── requirements.txt               # Pinned dependencies
  ├── pyproject.toml                 # Package definition & pytest config
  ├── .env.example                   # Environment variable template (no secrets)
  ├── .gitignore                     # Git exclusions
  ├── src/
  │   └── hakkuai/
  │       ├── __init__.py            # Package entry
  │       ├── agent.py               # Main uAgent definition, CLI & health server
  │       ├── config.py              # Configuration & environment loader
  │       ├── schemas.py             # Pydantic schemas & state models
  │       ├── logging_config.py      # Privacy-safe logger with PII masking
  │       ├── sources.py             # Government domain validation & citations
  │       ├── scheme_database.py     # Scheme loader, state indexing & filtering
  │       ├── eligibility.py         # Deterministic Python eligibility engine
  │       ├── document_checklist.py  # Personalized checklist with fallback evidence
  │       ├── injury_workflow.py     # Emergency 112 check, evidence preservation
  │       ├── conversation.py        # Progressive intake, session isolation, Tamil/English
  │       └── acp_handlers.py        # Official ACP ChatMessage handlers & Inter-Agent RPC
  ├── data/
  │   └── schemes.json               # Verified Indian welfare schemes registry
  ├── tests/
  │   ├── __init__.py
  │   ├── test_schemes.py            # Knowledge base and domain validation tests
  │   ├── test_eligibility.py        # Deterministic eligibility engine tests
  │   ├── test_injury_workflow.py    # Emergency check and injury flow tests
  │   ├── test_document_checklist.py # Personalized document checklist tests
  │   ├── test_conversation.py       # Progressive intake & session isolation tests
  │   └── test_protocol.py           # ACP protocol & 3 End-to-End hackathon scenarios
  └── docs/
      ├── ARCHITECTURE.md            # Deep system architecture & data flow
      ├── AGENTVERSE_SETUP.md        # Official Agentverse registration & mailbox guide
      ├── ACP_INTEGRATION.md         # ACP specification & message handling
      ├── ASI_ONE_SETUP.md           # ASI:One integration & discovery guide
      └── TESTING.md                 # Test suite details & scenario walkthroughs
```

---

## 5. Quickstart & Installation

### Prerequisites
- Python 3.11 installed
- Git installed

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/your-username/hakkuai.git
cd hakkuai

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy template (contains placeholders only)
cp .env.example .env
```
*(HakkuAI works locally out-of-the-box without requiring external paid API keys.)*

---

## 6. Running HakkuAI

### Mode A: Interactive Conversational Terminal (Recommended for Quick Demo)
Simulate worker conversations in English or Tamil directly in your terminal:
```bash
python src/hakkuai/agent.py --cli
```

### Mode B: Autonomous uAgent (Fetch.ai Network Daemon)
Starts the uAgent with ACP protocol listeners and Almanac registration:
```bash
python src/hakkuai/agent.py
```
*Output:*
```
2026-10-24 [INFO] [hakkuai] Loaded 6 verified welfare schemes from data/schemes.json
2026-10-24 [INFO] [hakkuai] ==================================================
2026-10-24 [INFO] [hakkuai]    HAKKUAI WELFARE ASSISTANCE AGENT (Fetch-A-Thon 3.0)
2026-10-24 [INFO] [hakkuai] ==================================================
2026-10-24 [INFO] [hakkuai] Agent Name    : hakkuai_welfare_assistant
2026-10-24 [INFO] [hakkuai] Agent Address : agent1qf3a2vppnvrg4txephs5ut9vn0x5tfyd87aer4fszxtlh35vj6ay7z4f2mr
2026-10-24 [INFO] [hakkuai] Listening Port: 8000
2026-10-24 [INFO] [hakkuai] ACP Protocol  : AgentChatProtocol v0.3.0 (Enabled)
2026-10-24 [INFO] [hakkuai] Ready for ASI:One & Agentverse communication.
2026-10-24 [INFO] [hakkuai] ==================================================
```

### Mode C: Auxiliary Health API Server
Launches an HTTP healthcheck endpoint for infrastructure monitoring:
```bash
python src/hakkuai/agent.py --health-server
```
Visit `http://localhost:8001/health` or `http://localhost:8001/schemes`.

---

## 7. Running Automated Tests

Run the complete test suite with 28 automated tests:

```bash
python -m pytest tests/ -v
```

All 28 tests pass in ~2 seconds, covering unit logic, state filtering, emergency handling, document checklists, ACP protocol message flows, and all 3 End-to-End demonstration scenarios.

---

## 8. Mandatory Fetch-A-Thon 3.0 End-to-End Scenarios

HakkuAI includes automated verification for all three required hackathon scenarios (tested in `tests/test_protocol.py`):

### Scenario 1: Registered Construction Worker with Workplace Injury
- **Context**: Worker in Tamil Nadu registered with the TNBOCW Welfare Board fractures leg in an on-duty accident.
- **HakkuAI Action**: Evaluates **Tamil Nadu BOCW Accident Relief Scheme** (`[Potentially eligible]`) and **Employees' Compensation Act 1923** (`[Potentially eligible]`). Outlines benefit amounts (up to ₹2,00,000 for disability), provides a document checklist with membership card and discharge summary, and directs worker to the District Labour Officer.

### Scenario 2: Unregistered Injured Worker (Employer Non-Cooperation)
- **Context**: Worker in Tamil Nadu suffered a workplace injury, but contractor refused to register them with the welfare board.
- **HakkuAI Action**: Explains that direct board benefits require registration (`[More information needed]`), but immediately activates **Employees' Compensation Act 1923** (`[Potentially eligible]`). Informs worker of statutory employer liability, explains how to petition the Commissioner for Employees' Compensation, and provides alternative evidence options (muster roll, supervisor chat logs, coworker affidavits).

### Scenario 3: Incomplete Local Database & Honest Uncertainty
- **Context**: Construction worker in Nagaland with a site injury.
- **HakkuAI Action**: Evaluates universal national schemes, but for the local state board, flags `[Unverified / Incomplete data]`. Explicitly informs the user: *"HakkuAI's local verified database does not currently contain verified state-specific benefit schedules for Nagaland. We do NOT fabricate benefit amounts."* Directs the worker to the official Nagaland Labour Commissioner Office without guessing.

---

## 9. ACP Implementation & ASI:One Integration

### Agent Chat Protocol (ACP v0.3.0)
HakkuAI implements the standard Fetch.ai chat protocol (`chat_protocol_spec`):
- Receives `ChatMessage` containing structured `TextContent`.
- Dispatches immediate delivery acknowledgment via `ChatAcknowledgement`.
- Returns structured conversational responses inside a reply `ChatMessage`.
- See [docs/ACP_INTEGRATION.md](docs/ACP_INTEGRATION.md) for full protocol schemas.

### ASI:One Discovery
- HakkuAI registers its protocol digest on the decentralized Almanac contract upon boot.
- Users in ASI:One can discover and chat with HakkuAI naturally in English or Tamil.
- See [docs/ASI_ONE_SETUP.md](docs/ASI_ONE_SETUP.md) for sample queries and indexing configuration.

### Agentverse Registration
- Supports running locally with an **Agentverse Mailbox** key for 24/7 cloud connectivity without port forwarding.
- See [docs/AGENTVERSE_SETUP.md](docs/AGENTVERSE_SETUP.md) for step-by-step registration instructions.

---

## 10. Verified Welfare Knowledge Base

HakkuAI indexes real, verified Indian welfare schemes with official government URLs:

| Scheme Name | Jurisdiction | Key Benefits | Official Source |
|---|---|---|---|
| **Tamil Nadu BOCW Welfare Board - Accident Relief** | Tamil Nadu | Up to ₹5,00,000 accidental death; ₹1,00,000 - ₹2,00,000 disability | [tnuwwb.tn.gov.in](https://tnuwwb.tn.gov.in) |
| **Employees' Compensation Act, 1923** | National | Formula-based employer statutory compensation (₹1,40,000 to ₹10,00,000+) | [labour.gov.in](https://labour.gov.in) |
| **Ayushman Bharat (AB-PMJAY / CMCHIS)** | National | Up to ₹5,00,000/year cashless secondary/tertiary hospital care | [pmjay.gov.in](https://pmjay.gov.in) |
| **Pradhan Mantri Suraksha Bima Yojana (PMSBY)** | National | ₹2,00,000 accidental death/total disability cover (₹20/year) | [financialservices.gov.in](https://financialservices.gov.in) |
| **e-Shram Social Security Registry** | National | 12-digit portable UAN Card & integrated accident insurance | [eshram.gov.in](https://eshram.gov.in) |
| **Karnataka BOCW Welfare Board - Accident Benefit** | Karnataka | Up to ₹5,00,000 accidental death; ₹2,00,000 permanent disability | [kbocwwb.karnataka.gov.in](https://kbocwwb.karnataka.gov.in) |

---

## 11. Known Limitations & Future Enhancements

1. **State Knowledge Base Coverage**: Verified state-specific BOCW benefit schedules are currently indexed for Tamil Nadu and Karnataka. For other states, HakkuAI provides national schemes and honest uncertainty notices. Future iterations will index all 28 states and 8 union territories.
2. **Audio/Voice Intake**: Many daily-wage workers are illiterate. Adding voice-to-text (Whisper) for spoken Tamil and Hindi input will enhance accessibility.
3. **Automated Claim Filing**: HakkuAI currently provides guided preparation and official office routing. Automatic form submission requires formal API integration with state e-Sevai / CSC portals.

---

## 12. Fetch-A-Thon 3.0 Submission Checklist

- [x] Functional uAgents agent with stable identity (`hakkuai_welfare_assistant`)
- [x] Official Agent Chat Protocol (ACP v0.3.0) compliant (`ChatMessage`, `ChatAcknowledgement`)
- [x] Dual-protocol support (ACP for ASI:One + Structured RPC for Inter-Agent querying)
- [x] Modular architecture with separated concerns (`src/hakkuai/...`)
- [x] Deterministic Python eligibility engine (no LLM hallucination of benefits)
- [x] Honest uncertainty handling when data is missing or state rules are unverified
- [x] Emergency medical safety prioritization (**National Emergency 112 / Ambulance 108**)
- [x] Guidance for unregistered workers under Employees' Compensation Act 1923
- [x] Personalized document checklist with fallback evidence
- [x] Official government domain validation (`.gov.in`, `.nic.in`)
- [x] Sensitive data sanitization and privacy-by-design
- [x] Bilingual English & Tamil (தமிழ்) conversational intake
- [x] 100% passing automated test suite (28/28 tests passed)
- [x] 3 End-to-End demonstration scenarios tested and documented
- [x] Zero hardcoded secrets, `.env.example` provided
- [x] Comprehensive documentation (`ARCHITECTURE.md`, `AGENTVERSE_SETUP.md`, `ACP_INTEGRATION.md`, `ASI_ONE_SETUP.md`, `TESTING.md`)

---

## 13. License

Distributed under the Apache 2.0 License. See `LICENSE` for details.
