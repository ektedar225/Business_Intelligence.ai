# VANTAGE — KPI Intelligence-to-Action Engine
### Comprehensive Technical & Functional Documentation

> **A production-grade Business Intelligence prototype** that ingests multi-source transactional data, resolves semantic discrepancies, detects and diagnoses material KPI movements, explains root causes in persona-tailored natural language, recommends authorized actions, and learns from analyst feedback — all with transparent uncertainty communication and zero-hallucination guarantees.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Repository Architecture & File Map](#2-repository-architecture--file-map)
3. [Quick Start & Setup Guide](#3-quick-start--setup-guide)
4. [End-to-End System Pipeline (L1 – L8)](#4-end-to-end-system-pipeline-l1--l8)
   - [L1: Data Reconciliation & Conformance](#l1-data-reconciliation--conformance)
   - [L2: Synthetic Data Generation](#l2-synthetic-data-generation)
   - [L3: Materiality & Detection Engine](#l3-materiality--detection-engine)
   - [L4: Attribution & Diagnosis Engine](#l4-attribution--diagnosis-engine)
   - [L5: Evidence Bundle (Deterministic Contract)](#l5-evidence-bundle-deterministic-contract)
   - [L6: Confidence & Responsible Abstention Gate](#l6-confidence--responsible-abstention-gate)
   - [L7: Narrative Generation & Numeric Firewall](#l7-narrative-generation--numeric-firewall)
   - [L8: Bayesian Feedback Loop & Driver Re-Ranking](#l8-bayesian-feedback-loop--driver-re-ranking)
5. [KPI Semantic Contract Registry](#5-kpi-semantic-contract-registry)
6. [Role-Based Persona Engine & Entitlements](#6-role-based-persona-engine--entitlements)
7. [Lever Registry & Action Composer](#7-lever-registry--action-composer)
8. [Google Gemini LLM Integration](#8-google-gemini-llm-integration)
9. [Conversational Intent & Grounded Q&A](#9-conversational-intent--grounded-qa)
10. [Proactive Alert Engine](#10-proactive-alert-engine)
11. [Data & Driver Drift Monitoring](#11-data--driver-drift-monitoring)
12. [Causal Inference (Difference-in-Differences)](#12-causal-inference-difference-in-differences)
13. [Cryptographic Audit Ledger](#13-cryptographic-audit-ledger)
14. [FastAPI REST API Reference](#14-fastapi-rest-api-reference)
15. [Single-Page Frontend UI (ChatGPT Dark Theme)](#15-single-page-frontend-ui-chatgpt-dark-theme)
16. [Demonstration Scenarios & Ground Truth](#16-demonstration-scenarios--ground-truth)
17. [Data Store & File Formats](#17-data-store--file-formats)
18. [Security, Governance & Anti-Hallucination Guarantees](#18-security-governance--anti-hallucination-guarantees)
19. [Testing & Verification](#19-testing--verification)
20. [Extensibility & Developer Guide](#20-extensibility--developer-guide)

---

## 1. Executive Summary

Traditional Business Intelligence (BI) platforms suffer from four core failure modes:
1. **Alert Storms & Noise**: Threshold-based alerts trigger on predictable seasonality or insignificant anomalies.
2. **Dashboard Fatigue & Lack of Diagnosis**: Dashboards report *what* moved, leaving analysts to spend hours manually slicing dimensions to discover *why*.
3. **GenAI Hallucinations**: Standard LLMs fabricate numbers, conflate correlation with causation, or leak restricted business data.
4. **Lack of Action & Closed Feedback**: Insights are disconnected from operational levers, with no mechanism to learn which recommendations worked.

**VANTAGE** addresses these challenges through a governed, multi-layered architecture:

| Challenge | VANTAGE Solution |
| :--- | :--- |
| **Alert Noise** | **Two-Axis Materiality**: Requires statistical surprise ($Z \ge 1.5$) AND business impact ($\Delta \ge \$2,000$) evaluated against seasonal baselines with hierarchy collapse. |
| **Diagnostic Attribution** | **Attribution Ladder**: Reconciles accounting bridges, event joins, and econometric estimators to quantify exact dollar contributions. |
| **Hallucination Risk** | **Numeric Firewall & Immutable Evidence Bundles**: LLMs receive strictly deterministic fact bundles and all output is parsed to block orphan numerals or unverified causal terms. |
| **Data Governance** | **Pre-Prompt Entitlements**: Row-level policies and column masking are applied directly to the Evidence Bundle before any LLM prompt is assembled. |
| **Action & Feedback** | **Beta-Bernoulli Prior Updates**: Analyst feedback on actions updates posterior driver weights to prioritize reliable explanations in future analyses. |

---

## 2. Repository Architecture & File Map

```
Business_Intelligence.ai/
├── api/
│   ├── main.py                   # FastAPI application & REST endpoint router
│   └── static/
│       └── index.html            # Responsive single-page UI (ChatGPT Dark theme)
├── vantage/
│   ├── __init__.py               # Package initializer
│   ├── actions.py                # Action composer, decision rights filter & escalations
│   ├── alerts.py                 # Proactive rule evaluation & multi-channel routing
│   ├── audit.py                  # SHA-256 hash-chained immutable audit ledger
│   ├── causal.py                 # Difference-in-Differences (DiD) Average Treatment Effect
│   ├── confidence.py             # 5-factor confidence scoring & 3 abstention modes
│   ├── contract_schema.py        # KPI contract validation & DAG integrity checks
│   ├── contracts/                # Declarative YAML semantic KPI contracts
│   │   ├── net_revenue.yaml
│   │   ├── gross_margin_pct.yaml
│   │   ├── units_sold.yaml
│   │   ├── asp.yaml
│   │   └── cac.yaml
│   ├── datagen.py                # Synthetic transaction, campaign & supply data generator
│   ├── diagnosis/                # L4 Attribution algorithms
│   │   ├── arithmetic_bridge.py  # Additive & multiplicative metric decomposition
│   │   ├── business_event.py     # Join engine linking movements to operational events
│   │   └── contribution.py       # Dimensional slicing & channel mix-shift analysis
│   ├── drift.py                  # Population Stability Index (PSI) & rank drift monitor
│   ├── evidence.py               # Immutable, content-hashed EvidenceBundle data model
│   ├── feedback.py               # Beta-Bernoulli learning-to-rank posterior updater
│   ├── intent.py                 # Natural language intent parser (Gemini + fallback)
│   ├── levers.yaml               # Governed decision levers & elasticity impact definitions
│   ├── llm.py                    # Resilient Google Gemini client with multi-model fallback
│   ├── materiality.py            # Seasonal baseline estimation & 2-axis quadrant router
│   ├── narrative.py              # Persona narrative synthesis & Numeric Firewall
│   ├── personas.yaml             # Governed roles, word budgets, scopes & lever rights
│   ├── pipeline.py               # Scenario builders (Scenarios 1, 2, 3, 4)
│   ├── reconciliation.py         # Calendar conformance, entity resolution & freshness
│   ├── registries.py             # Persona and Lever registry loaders
│   └── scorecard.py             # Post-action recovery scorecard tracker
├── data/
│   ├── orders.csv                # Synthetic order lines (~2.9 MB)
│   ├── marketing.csv             # Weekly marketing spend by region & channel
│   ├── supply.csv                # Hourly warehouse inventory snapshots (~5.5 MB)
│   ├── dim_sku.csv               # SKU product master hierarchy
│   ├── cac_new_family.csv        # Cold-start marketing & customer acquisition data
│   ├── driver_weights.json       # Persisted Beta-Bernoulli driver ranking weights
│   ├── feedback_log.jsonl        # Append-only feedback log
│   ├── audit_ledger.jsonl        # Cryptographic hash-chained audit ledger
│   └── ground_truth.json         # Benchmark events for test validation
├── tests/
│   ├── test_completion.py        # End-to-end integration and completion tests
│   ├── test_llm.py               # Gemini client, fallback & cost accounting tests
│   └── test_pipeline.py          # Scenario bundle validation & hashing tests
├── .env.example                  # Environment variable configuration template
├── .gitignore                    # Git exclusion rules (safely excludes .env)
├── README.md                     # Quick start & repository overview
└── VANTAGE_DOCUMENTATION.md     # Complete reference manual
```

---

## 3. Quick Start & Setup Guide

### 3.1 Prerequisites
- **Python**: 3.10 or higher
- **Dependencies**: `fastapi`, `uvicorn`, `pydantic`, `pyyaml`, `pandas`, `numpy`
- **Gemini API Key**: (Optional but recommended for generative features)

### 3.2 Installation

```bash
# 1. Clone the repository
git clone https://github.com/ektedar225/Business_Intelligence.ai.git
cd Business_Intelligence.ai

# 2. Install dependencies
pip install fastapi uvicorn pydantic pyyaml pandas numpy

# 3. Configure Gemini API Key
cp .env.example .env
# Open .env and insert your API key:
# GEMINI_API_KEY=your_gemini_api_key_here
```

### 3.3 Launching the Application

```bash
python3 -m uvicorn api.main:app --port 8000 --host 0.0.0.0 --reload
```

Navigate to **`http://127.0.0.1:8000`** in your web browser.

---

## 4. End-to-End System Pipeline (L1 – L8)

The engine executes an 8-stage deterministic-to-generative processing pipeline:

```
[ L1 Reconciliation ]  -->  [ L3 Materiality ]  -->  [ L4 Diagnosis ]
         │                          │                         │
         ▼                          ▼                         ▼
   Calendar/Entity          2-Axis Surprise &       Attribution Ladder
    Freshness SLAs           Impact Quadrants       (Bridge, Event, Mix)
                                                              │
                                                              ▼
[ L7 Narrative & Firewall ] <-- [ L6 Confidence Gate ] <-- [ L5 Evidence Bundle ]
         │                              │                         │
         ▼                              ▼                         ▼
  Persona Synthesis             Composite Score &         Content-Hashed
  & Numeric Checker             3 Abstention Modes        Immutable State
         │
         ▼
[ L8 Feedback Loop ]  -->  Updates Driver Weights  -->  Informs Next Run
```

---

### L1: Data Reconciliation & Conformance
**Module**: [`vantage/reconciliation.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/reconciliation.py)

- **Calendar Conformance**: Projects varying date formats onto the standard ISO Monday-start week calendar (`iso_week_start`), eliminating discrepancies between fiscal and Gregorian reporting.
- **Entity Resolution**: Joins transactional order lines against `dim_sku.csv`. Unmatched records accumulate in a tracked reconciliation residual rather than being silently dropped.
- **Freshness SLA Watermarking**: Each evidence fact is stamped with the freshness timestamp of the slowest contributing data source.
- **Grain-Safe Ratio Aggregation**: Enforces that ratio metrics (e.g., Gross Margin %, ASP) are computed strictly from aggregated components rather than averaged across dimensions.

---

### L2: Synthetic Data Generation
**Module**: [`vantage/datagen.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/datagen.py)

Generates 52 weeks of multi-region e-commerce data across EMEA, AMER, and APAC, embedding known operational shocks:
- **Promo End**: Targeted marketing promo withdrawal in Week 30 for AMER Family A.
- **Supply Chain Stockout**: Inventory depletion in Week 30 for SKU-4471 in DE warehouse.
- **Marketplace Mix Shift**: Channel migration toward lower-ASP third-party marketplaces.

---

### L3: Materiality & Detection Engine
**Module**: [`vantage/materiality.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/materiality.py)

Evaluates whether a metric deviation warrants executive escalation using a two-axis framework:
1. **Statistical Surprise ($Z$-score)**: Deviation against an 8-week seasonal baseline:
   $$\text{Baseline} = \frac{1}{N} \sum_{t=1}^{8} y_{t}, \quad Z = \frac{y_{\text{actual}} - \text{Baseline}}{\sigma_{\text{baseline}}}$$
2. **Business Impact ($\Delta \$$)**: Absolute dollar change week-over-week ($|\Delta_{\text{abs}}|$).

**Materiality Routing Quadrants**:
- **Alert & Full Diagnosis**: High Surprise ($|Z| \ge 1.5$) + High Impact ($|\Delta| \ge \$2,000$).
- **Digest (Expected but Large)**: Low Surprise + High Impact (e.g., expected seasonal holiday volume).
- **Weekly Digest**: High Surprise + Low Impact (statistically anomalous but financially minor).
- **Suppress**: Low Surprise + Low Impact (normal operating variance).

**Hierarchy Collapse**: Identifies when child regional movements stem from a single parent global event, collapsing multiple alerts into a single cohesive incident.

---

### L4: Attribution & Diagnosis Engine
**Directory**: [`vantage/diagnosis/`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/diagnosis/)

Applies a hierarchical attribution ladder to decompose the total delta into specific, quantified drivers:
1. **Arithmetic Bridge** (`arithmetic_bridge.py`): Decomposes revenue movements into Volume vs. Price effects:
   $$\Delta \text{Revenue} = \Delta \text{Units} \times \text{ASP}_{\text{base}} + \Delta \text{ASP} \times \text{Units}_{\text{base}} + \Delta \text{Units} \times \Delta \text{ASP}$$
2. **Business Event Join** (`business_event.py`): Correlates anomalies with operational changes (marketing campaigns, promo end dates, inventory stockouts).
3. **Dimensional Contribution & Mix** (`contribution.py`): Quantifies regional slicing and channel mix-shift effects.

---

### L5: Evidence Bundle (Deterministic Contract)
**Module**: [`vantage/evidence.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/evidence.py)

The `EvidenceBundle` is an immutable, content-hashed Pydantic model representing the single source of truth for an event:

```python
class EvidenceBundle(BaseModel):
    event_id: str
    kpi_id: str
    period: str
    as_of_watermark: str
    movement: MovementFact
    facts: list[EvidenceFact]
    residual: dict
    contradictions: list[Contradiction]
    confidence: Optional[ConfidenceBreakdown]
    entitlement_scope: Optional[EntitlementScope]
    telemetry: Optional[Telemetry]
    data_quality_flags: list[str]
    bundle_hash: str
```

- **Content Hashing**: Computes a deterministic SHA-256 hash across canonical bundle facts (`bundle_hash`), ensuring verification and reproducibility.
- **Pre-Prompt Entitlement Scoping**: Calling `bundle.scoped_to(...)` removes unentitled regional rows and masks sensitive columns **before** any LLM prompt is assembled.

---

### L6: Confidence & Responsible Abstention Gate
**Module**: [`vantage/confidence.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/confidence.py)

Calculates a 5-factor composite confidence score:
$$\text{Composite} = 0.25 \times C_{\text{data}} + 0.20 \times C_{\text{method}} + 0.25 \times C_{\text{coverage}} + 0.15 \times C_{\text{consistency}} + 0.15 \times C_{\text{history}}$$

| Band | Threshold | Action |
| :--- | :--- | :--- |
| **High** | $\ge 0.85$ | Unrestricted narrative generation and high-confidence action recommendations. |
| **Medium** | $0.65 - 0.849$ | Narrative generation with explicit caveat statements. |
| **Low** | $0.40 - 0.649$ | Narrative with prominent uncertainty banners and reduced action confidence. |
| **Abstain** | $< 0.40$ | Generation is blocked; triggers structured Responsible Abstention. |

**Three Abstention Modes**:
- **Mode A (Clarify)**: Triggered by ambiguous natural language queries (e.g., user asks for *"performance"* which could map to Revenue, Margin, or Units). Returns candidate clarification buttons.
- **Mode B (Competing Hypotheses)**: Triggered when multiple attribution methods show comparable support for contradictory drivers. Presents both hypotheses side-by-side with discriminating tests.
- **Mode C (Hard Abstain)**: Triggered by data quality SLA breaches (e.g., stale cost feeds). Declares exact blockers, data owner ETAs, and what data remains reliable.

---

### L7: Narrative Generation & Numeric Firewall
**Module**: [`vantage/narrative.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/narrative.py)

#### Model Routing:
- `T0_template`: Deterministic string interpolation (<5ms latency, $0 cost).
- `T1_small_model`: Fast conversational synthesis via `gemini-3.5-flash-lite`.
- `T2_frontier`: Capable reasoning via `gemini-2.5-pro` (used for complex contradictions).

#### Numeric Firewall & Zero-Hallucination Verification:
Every generated LLM response is processed through `verify_narrative()`:
1. All numerals in the generated text are extracted and verified against numbers in the `EvidenceBundle`.
2. Identifiers (`[E-01]`, `SKU-4471`, `week_30`) are recognized and excluded from numeral checks.
3. Causal verbs (*"caused"*, *"drove"*, *"resulted in"*) are verified against declared causal methods (`causal_did`).
4. **Guaranteed Fallback**: If an orphan numeral or ungrounded causal claim is detected, the engine blocks the text and falls back to the deterministic `T0_template`.

---

### L8: Bayesian Feedback Loop & Driver Re-Ranking
**Module**: [`vantage/feedback.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/feedback.py)

Implements a live-updating Beta-Bernoulli Bayesian update rule:
$$\text{Posterior Weight} = \frac{\text{Accepted} + 1}{\text{Accepted} + \text{Rejected} + 2}$$

- **Live Driver Re-Ranking**: Future diagnostic runs weight drivers by $(\text{Contribution Share} \times \text{Posterior Weight})$. Repeatedly rejected drivers drift down the attribution ranking.
- **Audit Persistence**: Every feedback action logs a structured record in `data/feedback_log.jsonl` and updates `data/driver_weights.json`.

---

## 5. KPI Semantic Contract Registry

**Module**: [`vantage/contract_schema.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/contract_schema.py)  
**Location**: `vantage/contracts/*.yaml`

Semantic contracts define KPIs as versioned, declarative YAML configurations:

```yaml
kpi_id: net_revenue
display_name: "Net Revenue"
definition_business: "Total revenue recognized from customer orders, net of returns and discounts"
formula: "SUM(order_value) - SUM(returns)"
grain:
  entity: order_line
  time: iso_week
calendar: iso_week
additivity: additive
hierarchy:
  parent: null
  children: [gross_margin_pct, units_sold]
  decomposition: arithmetic
dimensions: [region, channel, product_family, sku]
registered_drivers:
  - id: promo_calendar
    type: controllable
    lever: promo_depth
    lag_days: [0, 14]
  - id: stockout_rate
    type: controllable
    lever: safety_stock
    lag_days: [0, 7]
  - id: channel_mix
    type: controllable
    lever: channel_incentive
    lag_days: [0, 21]
materiality:
  min_business_impact_usd: 2000
  min_surprise_z: 1.5
  min_history_periods: 6
lineage:
  - orders.csv::order_value
  - orders.csv::returns
entitlements:
  row_policy: region_equals_persona_territory
  column_masks:
    customer_segment: regional_director_emea
freshness_sla_hours: 24.0
version: 1
```

---

## 6. Role-Based Persona Engine & Entitlements

**Configuration**: [`vantage/personas.yaml`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/personas.yaml)

Personas govern language complexity, length budgets, regional row access, and column masking:

| Persona ID | Display Name | Vocabulary | Word Budget | Regional Scope | Masked Columns | Authorized Levers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `cfo` | CFO | Executive | 90 words | Global (EMEA, AMER, APAC) | None | Decisions Only |
| `regional_director_emea` | Regional Sales Director | Operational | 140 words | EMEA Only | `customer_segment` | `channel_incentive` |
| `category_manager` | Category Manager | Operational | 160 words | Global | None | `promo_depth`, `safety_stock` |
| `analyst` | Data Analyst | Technical | 400 words | Global | None | Model Config / Contracts |

---

## 7. Lever Registry & Action Composer

**Module**: [`vantage/actions.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/actions.py)  
**Configuration**: [`vantage/levers.yaml`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/levers.yaml)

- **Grounded Action Generation**: Actions are drawn from a curated registry rather than being invented by an LLM.
- **Decision Rights Filtering**: Levers outside a persona's decision rights generate structured escalations to the appropriate role (e.g., an unentitled promo change is escalated to the Category Manager).
- **Elasticity Confidence Intervals**: Each action includes an empirical point estimate and confidence interval (e.g., `+4.5%` impact, CI `[+2.8%, +6.2%]`).

---

## 8. Google Gemini LLM Integration

**Module**: [`vantage/llm.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/llm.py)

- **Zero Third-Party SDK Overhead**: Implemented directly using Python's standard library `urllib.request`.
- **Automatic Multi-Model Fallback Chain**:
  - `gemini-3.5-flash-lite` $\rightarrow$ `gemini-3.1-flash-lite` $\rightarrow$ `gemini-3.5-flash` $\rightarrow$ `gemini-flash-latest`
- **Telemetry Accounting**: Automatically tracks input tokens, output tokens, latency (ms), and exact dollar cost per API call.

---

## 9. Conversational Intent & Grounded Q&A

**Module**: [`vantage/intent.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/intent.py)

- **Dual-Path Resolution**: Combines structured regex/synonym dictionaries with Gemini JSON intent parsing.
- **Grounded Executive Answers**: `/api/ask` synthesizes answers directly from the Evidence Bundle with clickable evidence tags (`[E-01]`, `[E-02]`).
- **Ambiguity Detection**: Queries like *"How is the business performing?"* return Mode A abstention with disambiguation chips.

---

## 10. Proactive Alert Engine

**Module**: [`vantage/alerts.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/alerts.py)

Evaluates Evidence Bundles against rules to produce structured alerts:
- **`high-surprise-z`**: Triggered when $|Z| \ge 2.0$ (Severity: Critical $\rightarrow$ Email/Dashboard).
- **`large-wow-move`**: Triggered when $|\Delta_{\text{WoW}}| \ge 5\%$ (Severity: Warning $\rightarrow$ Dashboard).
- **`low-confidence-alert`**: Triggered when confidence falls to `low` or `abstain` (Severity: Warning $\rightarrow$ Slack/Analyst).
- **`net-revenue-critical-drop`**: Triggered when Net Revenue drops $\ge 8\%$ WoW (Severity: Critical $\rightarrow$ CFO Email).

---

## 11. Data & Driver Drift Monitoring

**Module**: [`vantage/drift.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/drift.py)

- **Population Stability Index (PSI)**: Monitors distribution shifts in KPI series across rolling time windows:
  $$\text{PSI} = \sum \left( P_i - Q_i \right) \times \ln\left(\frac{P_i}{Q_i}\right)$$
  - $\text{PSI} < 0.10$: Stable | $0.10 \le \text{PSI} \le 0.25$: Moderate Drift | $\text{PSI} > 0.25$: Significant Shift.
- **Driver Rank Drift**: Evaluates Spearman rank correlation across historical driver acceptance weights to detect concept drift.

---

## 12. Causal Inference (Difference-in-Differences)

**Module**: [`vantage/causal.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/causal.py)

Quantifies the Average Treatment Effect (ATE) of business interventions:
$$\text{ATE}_{\text{DiD}} = \left(\bar{y}_{\text{treated, post}} - \bar{y}_{\text{treated, pre}}\right) - \left(\bar{y}_{\text{control, post}} - \bar{y}_{\text{control, pre}}\right)$$

- Evaluates parallel trends across pre-period baseline windows.
- Outputs 95% confidence intervals, assumptions, and methodological limitations.

---

## 13. Cryptographic Audit Ledger

**Module**: [`vantage/audit.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/audit.py)  
**Ledger File**: `data/audit_ledger.jsonl`

Every delivered narrative, user action, and feedback event is logged into an append-only, SHA-256 hash-chained ledger:
$$\text{Entry Hash} = \text{SHA-256}\left(\text{Prev Hash} + \text{Canonical JSON Payload}\right)[:16]$$

`audit.verify_chain()` allows verification of the entire historical chain to detect any retroactive data tampering.

---

## 14. FastAPI REST API Reference

**Module**: [`api/main.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/api/main.py)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check endpoint returning `{"status": "ok"}`. |
| `/api/scenario/{id}` | `GET` | Executes pipeline for Scenario ID (`1`–`4`), scoped by `persona_id` and `use_llm`. |
| `/api/ask` | `POST` | Natural language query endpoint; returns resolved KPI, grounded answer, or abstention. |
| `/api/feedback` | `POST` | Submits analyst feedback (`accept`/`reject`); updates Beta-Bernoulli weights. |
| `/api/contracts` | `GET` | Returns all registered and validated semantic KPI contracts. |
| `/api/personas` | `GET` | Returns all registered persona definitions, word budgets, and scopes. |
| `/api/telemetry` | `GET` | Returns aggregated LLM latency, token counts, and cost telemetry. |
| `/api/audit` | `GET` | Retrieves recent cryptographically chained audit log entries. |
| `/api/alerts/{id}` | `GET` | Returns triggered alert rules and delivery statuses for a scenario. |
| `/api/drift/{id}` | `GET` | Evaluates PSI data drift and driver rank correlation. |
| `/api/causal/{id}` | `GET` | Computes DiD causal Average Treatment Effect for scenario interventions. |
| `/api/reconciliation`| `GET` | Returns source freshness audits and naive vs. governed aggregation comparisons. |

---

## 15. Single-Page Frontend UI (ChatGPT Dark Theme)

**File**: [`api/static/index.html`](file:///Users/apple/Documents/project/Business_Intelligence.ai/api/static/index.html)

- **Aesthetic**: Modern dark mode interface (`#0d0d0d` background, `#171717` card containers, `#10a37e` accent colors).
- **Narrative Controls**: Includes a `Gemini AI` vs. `Template (T0)` mode switch, along with a `Regenerate` button.
- **LLM Telemetry Ribbon**: Real-time display of active model, latency, token usage, cost, and firewall integrity badge.
- **Interactive Action Feedback**: Immediate state updates on buttons (`Accepted`/`Rejected`) with floating toast notifications.
- **Deep Dive Tabs**: Dedicated sub-panels for Reconciliation, Alerts, Drift, Causal Inference, Scorecard, and Contracts.

---

## 16. Demonstration Scenarios & Ground Truth

**Module**: [`vantage/pipeline.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/pipeline.py)

### Scenario 1: Multi-Factor Revenue Drop
- **KPI**: Net Revenue ($\Delta = -\$5,758$ or $-8.7\%$ WoW in Week 30).
- **Drivers**:
  - `[E-01]`: AMER promo campaign `CMP-family_a-AMER` ended ($- \$3,774$).
  - `[E-02]`: SKU-4471 stockout in DE warehouse ($- \$1,637$).
  - `[E-03]`: Channel mix shift toward lower-ASP marketplace ($- \$748$).
  - `[E-04]`: Residual noise ($+ \$402$).
- **Outcome**: High Confidence (0.92). Generates actions for promo restart, stockout replenishment, and channel incentives.

### Scenario 2: Responsible AI Hard Abstention
- **KPI**: Gross Margin %.
- **Blocker**: Hourly inventory/cost feed is 38 hours stale against a 24-hour freshness SLA.
- **Outcome**: Mode C Hard Abstain. Suppresses corrupted margin computation while presenting reliable revenue facts.

### Scenario 3: Cold Start & Sparse History
- **KPI**: Customer Acquisition Cost (CAC) for a newly launched product family.
- **Limitation**: Only 4 weeks of operational history (minimum required: 8).
- **Outcome**: Confidence capped at Medium (0.649); narrative explicitly flags baseline uncertainty.

### Scenario 4: Competing Hypotheses
- **KPI**: Net Revenue.
- **Conflict**: Dimensional contribution attributes drop to Price compression, while Event Join attributes drop to Marketing budget cuts.
- **Outcome**: Mode B Abstention. Presents both competing hypotheses with recommended discriminating tests.

---

## 17. Data Store & File Formats

- **`data/orders.csv`**: Transaction lines (`order_id`, `date`, `sku`, `region`, `channel`, `order_value`, `returns`, `units`).
- **`data/marketing.csv`**: Campaign spend and events (`week_start`, `region`, `channel`, `spend`, `campaign_id`).
- **`data/supply.csv`**: Hourly warehouse snapshots (`timestamp`, `warehouse`, `sku`, `stock_level`, `stockout_flag`).
- **`data/dim_sku.csv`**: Master product hierarchy (`sku`, `product_family`, `category`, `base_price`).
- **`data/driver_weights.json`**: Learned Beta-Bernoulli posterior weights.
- **`data/feedback_log.jsonl`**: Structured JSONL feedback log.
- **`data/audit_ledger.jsonl`**: Cryptographic SHA-256 hash-chained JSONL audit ledger.

---

## 18. Security, Governance & Anti-Hallucination Guarantees

1. **Pre-Prompt Row/Column Governance**: Row-level policies (`region_equals_persona_territory`) and column masks are executed on Python objects before any prompt is assembled.
2. **Deterministic-Only Numeric Pipeline**: LLMs do not perform arithmetic; all values originate from validated Evidence Bundles.
3. **Numeric Firewall Verification**: Prevents any orphan numbers or ungrounded causal claims from reaching end users.
4. **Append-Only Tamper-Evident Auditing**: SHA-256 hash chaining guarantees detection of any retroactive audit log modification.

---

## 19. Testing & Verification

Execute the test suite using `pytest`:

```bash
python3 -m pytest tests/ -v
```

- **`tests/test_pipeline.py`**: Verifies deterministic Evidence Bundle creation, content hashing, and entitlement scoping.
- **`tests/test_completion.py`**: Validates end-to-end execution across all 4 scenarios, verifying narrative structures, firewall enforcement, and action plan compositions.
- **`tests/test_llm.py`**: Tests Gemini API key discovery, fallback cascades, token accounting, and cost tracking.

---

## 20. Extensibility & Developer Guide

### Adding a New KPI
1. Create a declarative contract at `vantage/contracts/<kpi_name>.yaml`.
2. Define grain, formula, hierarchy, drivers, materiality thresholds, and entitlements.
3. Register driver identifiers in `vantage/feedback.py` (`REGISTERED_DRIVER_IDS`).
4. Add natural language aliases in `vantage/intent.py` (`SYNONYMS`).

### Adding a New Decision Lever
1. Append the lever definition to `vantage/levers.yaml`.
2. Specify `lever_id`, `driver_id`, `owner_role`, `expected_impact`, `lead_time_days`, and `constraints`.
3. Grant decision rights to target personas in `vantage/personas.yaml`.

### Wiring Production Alert Transports
In [`vantage/alerts.py`](file:///Users/apple/Documents/project/Business_Intelligence.ai/vantage/alerts.py), update `deliver_alerts()` to forward messages to SendGrid, Slack Webhooks, or PagerDuty without altering the upstream evaluation logic.
