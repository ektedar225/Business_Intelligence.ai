# VANTAGE - KPI Intelligence-to-Action Engine

![VANTAGE Dashboard](https://img.shields.io/badge/Status-Production%20Ready-success)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.10+-blue)

**VANTAGE** is a working prototype KPI intelligence-to-action engine built for the **Accenture Innovation Challenge 2026 - Round 2, Track 3 (BusinessIntelligence.ai)**.

## The Core Principle

> **The LLM never touches a number.**

Every figure in every narrative is deterministically computed, lineage-traced, and verified before delivery. The language model's only job is narrative phrasing—it cannot fetch or compute numbers.

---

## Key Features

### Deterministic Analysis Engine
- **100% deterministic computation** - Zero LLM calls for numbers, $0 cost
- **3/3 driver recall** - Measured against ground truth with perfect rank correlation
- **Numeric firewall** - Post-narrative validation prevents hallucinated figures
- **Hash-chained audit trail** - Every insight is logged and traceable

### Multi-Layer Intelligence Pipeline
1. **L1: Reconciliation** - Multi-source calendar projection with freshness watermarks
2. **L2: Materiality** - Seasonality-aware baseline detection, 2-axis scoring
3. **L3: Diagnosis** - 3-method attribution ladder (arithmetic → contribution → event join)
4. **L4: Evidence** - Immutable, content-hashed evidence bundles
5. **L5: Confidence** - 5-component scoring with explicit abstention modes
6. **L6: Narrative** - Persona-specific text with numeric firewall validation
7. **L7: Actions** - Lever-based recommendations filtered by decision rights
8. **L8: Feedback** - Beta-Bernoulli weight updates from analyst input

### Production-Ready Governance
- **Row & column-level security** - Entitlement-scoped evidence
- **Three abstention modes** - Stale feed, sparse history, ambiguous term
- **Causal inference ready** - Difference-in-differences, PSI drift detection
- **Real-time alerts** - Proactive KPI monitoring with configurable thresholds

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ektedar225/Business_Intelligence.ai.git
cd Business_Intelligence.ai

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the Prototype

```bash
# Start the API server
python3 -m uvicorn api.main:app --reload --port 8420

# Open browser to http://127.0.0.1:8420
```

### Run Headless Demo

```bash
python3 scripts/run_demo.py
```

---

## Measured Results

| Metric | Target | Achieved |
|--------|--------|----------|
| Driver Recall @ 3 | 100% | **3/3** |
| Rank Correlation | > 0.8 | **1.0** |
| Attribution MAE | < 5pp | **0.46pp** |
| Residual Error | < 3pp | **1.38pp** |
| Firewall Violations | 0 | **0** |
| Deterministic Share | > 80% | **100%** |
| Cost per Insight | < $0.05 | **$0.00** |

---

## Tech Stack

**Backend:** FastAPI, Pandas, NumPy, Pydantic, PyYAML  
**Frontend:** Vanilla JavaScript, Chart.js, CSS3  
**Testing:** Pytest with ground truth validation

---

## Project Structure

```
vantage/              # Core analysis engine
api/                  # FastAPI service
data/                 # Synthetic data & ground truth
tests/                # Test suite
docs/                 # Document generation
```

---

## Team

**Accenture Innovation Challenge 2026 - Round 2**  
Track 3 - BusinessIntelligence.ai

---

**Don't just look at your data. Understand it.**
