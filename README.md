# VANTAGE — KPI Intelligence-to-Action Engine

VANTAGE is a working prototype built for Round 2 of the Accenture Innovation Challenge. The brief asked for a system that can look at a KPI movement, explain what actually caused it with evidence, say plainly when it doesn't know enough to explain it, and turn that explanation into an action a specific person is allowed to take. This repository is that system: a Python backend that does the detection, reconciliation, driver attribution, confidence scoring, and narrative generation, sitting behind a small FastAPI service with a browser dashboard on top.

The supporting business proposal and pitch deck for the submission are also included in the repository root (`VANTAGE_Business_Proposal.pdf` / `.docx` and `VANTAGE_Pitch_Deck.pptx`).

## Approach

The core design decision behind VANTAGE is that the language model, where one is used at all, is never allowed to touch a number. Every figure that ends up in a narrative — the size of a movement, the share attributed to a driver, a confidence score — is computed by deterministic, testable Python code first and handed to the text layer as an immutable, already-verified object. The narrative layer's only job is to phrase that object in a way that fits the reader, and a numeric firewall checks afterwards that every number in the rendered text actually traces back to the evidence bundle it was given. In this prototype the default narrative tier is template-based and makes zero model calls at all, which is the strongest version of that guarantee: it isn't that the model is well-behaved, it's that it's architecturally absent from the money path.

The second design decision is to treat "we don't know" as a real output, not a failure state. When a source feed is stale, when history is too sparse to trust a pattern, or when a business term is genuinely ambiguous, the engine abstains explicitly and says what evidence is missing and what would resolve it, rather than guessing and sounding confident about it.

Everything downstream of that — which KPIs exist, who is allowed to see what, which levers a persona can pull — is driven by plain YAML config (`vantage/contracts/`, `vantage/personas.yaml`, `vantage/levers.yaml`) rather than hardcoded logic, so extending the system to a new metric or a new role is a config change, not a code change.

## Architecture

The pipeline is organized as a layered ladder, with each layer implemented as a small, independently testable module under `vantage/`:

- **L1 — Reconciliation** (`reconciliation.py`): projects heterogeneous sources (daily orders, weekly marketing, hourly supply snapshots) onto one calendar, resolves SKUs to a conformed product dimension, and watermarks every fact with the freshness of its slowest contributing source.
- **L3 — Materiality** (`materiality.py`): detects which KPI movements are actually worth explaining, using a seasonality-aware baseline and two-axis materiality (statistical surprise and business impact) instead of a single fixed threshold. Also collapses a global movement and its regional children into one event instead of an alert storm.
- **Diagnosis method ladder** (`vantage/diagnosis/`): three complementary attribution techniques, run cheapest and most-certain first —
  - `arithmetic_bridge.py`: exact price/volume/mix decomposition (pure algebra, not inference).
  - `contribution.py`: dimensional slice attribution via beam search over the dimension lattice, plus mix-variance effects.
  - `event_join.py`: joins registered operational events (promo end, stockout) onto the movement window to find a business-event explanation.
  - `residual.py`: whatever the ladder can't explain is stated explicitly as an unexplained residual instead of being folded silently into the last driver found.
- **L5 — Evidence Bundle** (`evidence.py`): the contract between the deterministic pipeline and the narrative layer — an immutable, typed, content-hashed object. The narrative service receives only this bundle, with no database access, so it cannot fetch or compute a number on its own.
- **L6 — Confidence & Abstention** (`confidence.py`): combines five named components into one banded composite score, and implements three distinct abstention behaviours (stale source, sparse history, ambiguous term) that each explain what's missing rather than just refusing.
- **L7 — Narrative & Numeric Firewall** (`narrative.py`): renders the persona-specific narrative and verifies afterwards that every numeral in the text is traceable to the evidence bundle and that no unproven causal language slipped in.
- **Action composition** (`actions.py`): actions are drawn from the lever registry, never invented by the narrative layer, and filtered by what the current persona is actually allowed to do; a material driver outside a persona's decision rights becomes an escalation instead of a suggested action they can't take.
- **L8 — Feedback loop** (`feedback.py`): an analyst's accept/reject on a specific driver is persisted and folded into a per-driver acceptance weight via a Beta-Bernoulli posterior update, so rejecting a driver repeatedly measurably lowers its rank on the next run.
- **Audit ledger** (`audit.py`): an append-only, hash-chained log of every delivered insight, so any result can be replayed from its bundle hash and any retroactive edit to the log is detectable.
- **Orchestration** (`pipeline.py`): the only module that knows the order the analyzers run in for each of the three demo scenarios; every analyzer itself is a pure, stateless function.
- **Scoring** (`scorecard.py`): because Scenario 1's data is generated with known, injected drivers (see `datagen.py`), this measures whether the engine actually recovers those drivers rather than just producing plausible-sounding text — driver recall, rank correlation, attribution error, and residual error are all computed against ground truth, not asserted.

`api/main.py` is a thin FastAPI layer over this pipeline: it resolves intent, scopes the evidence bundle to the requesting persona's entitlements, and returns the narrative, actions, firewall verdict, and telemetry as JSON. `api/static/index.html` is the browser dashboard served from the same app.

### Repository layout

```
vantage/            Core engine: reconciliation, materiality, diagnosis, confidence, narrative, actions, feedback, audit
vantage/contracts/  YAML KPI contracts (definition, grain, driver DAG, materiality thresholds, entitlements)
vantage/diagnosis/  The three-method attribution ladder plus residual accounting
api/                FastAPI service and static dashboard
data/                Synthetic source data and generated ground truth / audit ledger
scripts/run_demo.py Headless end-to-end run of all three scenarios (no browser needed)
tests/               Pytest suite covering the pipeline
docs/                Node scripts that generate the business proposal and pitch deck documents
```

## Dependencies

Backend (Python 3.10+):

- fastapi
- uvicorn
- pandas
- numpy
- pydantic
- PyYAML
- pytest (for the test suite)

All pinned in `requirements.txt`.

Document generation (`docs/`) uses Node.js with `docx` and `pptxgenjs`, listed in `package.json`. This part is only needed if you want to regenerate the proposal or pitch deck; it isn't required to run the engine itself.

## Running it

Clone the repository and set up a Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the headless demo, which regenerates the synthetic data with injected ground truth and runs all three scenarios end to end, printing the narrative, the recovery scorecard, and the firewall verdict:

```bash
python3 scripts/run_demo.py
```

Start the API and dashboard:

```bash
python3 -m uvicorn api.main:app --reload --port 8420
```

Then open `http://127.0.0.1:8420` in a browser. A few endpoints worth trying directly:

- `GET /api/scenario/1?persona_id=cfo` — the multi-factor Net Revenue movement, fully explained
- `GET /api/scenario/2?persona_id=cfo` — the stale-feed abstention scenario
- `GET /api/scenario/3?persona_id=cfo` — the sparse-history CAC scenario
- `GET /api/firewall-demo` — shows the numeric firewall catching a deliberately corrupted narrative
- `GET /api/audit` — the hash-chained audit ledger with chain-validity check

Run the test suite:

```bash
pytest tests/ -v
```

To regenerate the business proposal or pitch deck from the `docs/` scripts:

```bash
npm install
node docs/build_proposal.js
node docs/build_pitch.js
```
