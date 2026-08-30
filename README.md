# VANTAGE — KPI Intelligence-to-Action Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg)](https://deepmind.google/technologies/gemini/)
[![Tests](https://img.shields.io/badge/pytest-15%20passed-success.svg)](file:///tests)

**VANTAGE** is an end-to-end KPI Intelligence-to-Action engine. Traditional Business Intelligence dashboards only display *what* happened; VANTAGE determines *why* it happened with mathematical evidence, knows when to abstain if evidence is incomplete, and translates root-cause diagnoses into concrete, authorized actions tailored to specific decision-makers.

---

## Core Design Philosophy

### 1. "The LLM Never Touches a Number"
Language models, when unconstrained, hallucinate figures and invent spurious correlations. In VANTAGE:
- **100% Deterministic Math**: All metric reconciliations, Price-Volume-Mix decompositions, lattice attributions, and confidence scores are calculated exclusively by deterministic Python algorithms.
- **Immutable Evidence Bundle**: The computed facts are sealed into a content-hashed, immutable `EvidenceBundle`.
- **Restricted AI Synthesis**: Google Gemini (or local template tiers) receives only the immutable bundle to synthesize persona-tailored prose. The LLM has zero direct access to databases or calculations.
- **Numeric Firewall**: An automated verification gate scans the output text before delivery to guarantee that every single numeral is traceable to the bundle and that no unproven causal claims are made.

```
┌─────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐     ┌───────────────────────┐
│ Raw Heterogeneous Data  │ ──► │  Deterministic Ladder  │ ──► │ Immutable Evidence     │ ──► │ Google Gemini LLM     │
│ (Orders, S3, ERP, Logs) │     │ (Math, PVM, DiD, PSI)  │     │ Bundle (Content-Hashed)│     │ Persona Narrative Gen │
└─────────────────────────┘     └────────────────────────┘     └────────────────────────┘     └───────────┬───────────┘
                                                                                                          │
                                                               ┌────────────────────────┐                 ▼
                                                               │ Governed User Delivery │ ◄── ┌───────────────────────┐
                                                               │ (Actions, UI, Alerts)  │     │ Numeric Firewall Gate │
                                                               └────────────────────────┘     │ (Zero Hallucination)  │
                                                                                              └───────────────────────┘
```

### 2. First-Class Abstention ("We Don't Know")
Rather than hallucinating answers when signals are weak, VANTAGE treats **"We Don't Know"** as a first-class governed output:
- **Mode A (Stale Feed)**: Identifies delayed upstream data feeds and watermarks.
- **Mode B (Sparse History / Competing Hypotheses)**: Flags insufficient statistical variance or unresolved cross-elasticity.
- **Mode C (Ambiguous Terminology)**: Asks for clarification when business terms (e.g., "Margin" vs "Gross Margin %") are unclear.

---

## Architectural Layers

VANTAGE is engineered as a layered pipeline (`vantage/`):

- **L1 — Reconciliation & Freshness Watermarking** (`reconciliation.py`): Projects heterogeneous sources onto a unified calendar, resolves SKUs to conformed product dimensions, and calculates pipeline freshness watermarks.
- **L3 — Seasonality-Aware Materiality** (`materiality.py`): Detects anomalous movements using statistical surprise ($z$-score against seasonal baselines) combined with absolute business materiality.
- **Diagnosis Ladder** (`vantage/diagnosis/`):
  - `arithmetic_bridge.py`: Exact algebraic Price-Volume-Mix (PVM) decomposition.
  - `contribution.py`: Multi-dimensional slice attribution via beam search over dimension lattices.
  - `event_join.py`: Operational event correlation (promotional end-dates, stockouts, supply delays).
  - `residual.py`: Explicitly accounts for unexplained variance rather than forcing false closures.
- **Causal Econometrics** (`causal.py`): **Difference-in-Differences (DiD)** regression estimating the true **Average Treatment Effect (ATE)** of business interventions.
- **Drift Detection** (`drift.py`): **Population Stability Index (PSI)** calculation across weekly metric distributions and driver rank volatility.
- **L5 — Evidence Bundle Contract** (`evidence.py`): Typed, serialized, content-hashed contract encapsulating all verified facts and telemetry.
- **L6 — Composite Confidence & Abstention Engine** (`confidence.py`): Five-factor confidence scoring (freshness, history length, completeness, signal-to-noise, lattice coverage).
- **L7 — Persona Adaptation & Numeric Firewall** (`narrative.py`): Persona-scoped narrative generation with word budgets, depth controls, and regex/token mathematical verification.
- **Decision Levers & Action Routing** (`actions.py`): Filters concrete operational actions from a YAML lever registry against the user's role-based decision rights.
- **L8 — Closed-Loop Feedback** (`feedback.py`): Beta-Bernoulli Bayesian posterior updates that learn from human analyst feedback (accept/reject) to dynamically adjust driver rankings.
- **Cryptographic Audit Ledger** (`audit.py`): Append-only, SHA-256 hash-chained ledger recording every insight, evidence hash, model version, and user action.
- **Proactive Multi-Channel Alerts** (`alerts.py`): Configurable rule evaluation and multi-channel delivery routing (Slack, Teams, Email).
- **Conversational Intent Router** (`intent.py` & `llm.py`): Natural language parser powered by Google Gemini with fallback to deterministic pattern matching.

---

## Getting Started

### 1. Environment Setup

Clone the repository and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables (Optional for LLM)

Create a `.env` file in the root directory to enable Google Gemini-powered dynamic narratives:

```bash
GEMINI_API_KEY="your-google-gemini-api-key"
```

*(Note: If no API key is provided, VANTAGE automatically operates in its high-speed **T0 Deterministic Template Tier** with zero external dependencies).*

### 3. Run the Headless Sanity Check

Regenerates synthetic data with ground truth and executes all scenarios end-to-end:

```bash
python3 scripts/run_demo.py
```

### 4. Launch the Interactive Dashboard

```bash
python3 -m uvicorn api.main:app --reload --port 8420
```

Open **`http://127.0.0.1:8420`** in your browser.

---

## Interactive Web Dashboard & Demo Scenarios

The browser dashboard demonstrates the full power of VANTAGE across four distinct scenarios:

1. **Scenario 1 · Multi-Factor Movement (Net Revenue)**: Decomposes a multi-driver revenue change into exact Price, Volume, Mix, and Stockout effects.
2. **Scenario 2 · Explicit Abstention (Stale S3 Pipeline)**: Demonstrates responsible AI by abstaining when upstream data is delayed.
3. **Scenario 3 · Sparse History (New Market CAC)**: Explains low confidence on metrics with short baselines.
4. **Scenario 4 · Competing Hypotheses (Margin Compression)**: Explicitly surfaces competing drivers when variance cannot be uniquely resolved.

### Interactive Features:
- **Persona Switcher**: Toggle between **CFO** (90-word executive summary), **Regional Sales Director** (region-masked, operational focus), and **Data Analyst** (full statistical grain).
- **Clickable Evidence Drawer**: Click chips like `[E-01]` or `[E-02]` to view immutable source facts.
- **Live Firewall Demo**: Click *"Run live violation-injection demo"* to watch the Numeric Firewall intercept and block synthetic hallucinations in real time.
- **Bayesian Feedback Loop**: Click Accept / Reject on drivers to watch posterior weights update dynamically.
- **Causal DiD & Data Drift (PSI)**: Inspect econometric treatment effects and weekly population stability indices.
- **Ask VANTAGE**: Natural language conversational entry point mapping questions directly to governed KPI contracts.

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status. |
| `GET` | `/api/contracts` | List all registered YAML KPI contracts. |
| `GET` | `/api/personas` | List persona definitions, decision rights, and masking rules. |
| `GET` | `/api/scenario/{id}?persona_id={p}` | Full diagnostic bundle, narrative, actions, and firewall verdict. |
| `GET` | `/api/scenario/1/scorecard` | Measured driver recall, rank correlation, and attribution MAE. |
| `GET` | `/api/causal` | Difference-in-Differences Average Treatment Effect (ATE). |
| `GET` | `/api/drift` | Population Stability Index (PSI) and driver rank drift metrics. |
| `GET` | `/api/alerts` | Proactively evaluated alert triggers across active metrics. |
| `GET` | `/api/firewall-demo` | Live side-by-side demonstration of the Numeric Firewall. |
| `POST`| `/api/feedback` | Submit analyst feedback to update Beta-Bernoulli weights. |
| `GET` | `/api/feedback/weights` | Current posterior driver weights and recent feedback logs. |
| `GET` | `/api/audit` | Append-only hash-chained audit ledger with SHA-256 chain verification. |
| `POST`| `/api/ask` | Natural language intent resolution to governed KPIs. |
| `GET` | `/api/telemetry` | End-to-end performance, wall-clock latency, and token cost metrics. |

---

## Testing

Run the full pytest suite:

```bash
pytest tests/ -v
```

All 15 unit and integration tests validate the attribution ladder, causal DiD, PSI drift, Gemini LLM fallback, numeric firewall interception, persona masking, and Bayesian feedback updating.

---

## Proposal & Pitch Deck Generation

Document generation scripts are available under `docs/`:

```bash
npm install
node docs/build_proposal.js   # Generates VANTAGE_Business_Proposal.docx
node docs/build_pitch.js      # Generates VANTAGE_Pitch_Deck.pptx
```

