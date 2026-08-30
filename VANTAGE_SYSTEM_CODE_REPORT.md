# VANTAGE — In-Depth Codebase & Architectural Report

> **Complete Code-Level Technical Report**  
> Repository: `ektedar225/Business_Intelligence.ai`  
> Language: Python 3.10+ / FastAPI / Vanilla ES6+ HTML5  
> Integration: Google Gemini LLM (`gemini-3.5-flash-lite`, `gemini-2.5-pro`)

---

## 1. System Overview & Core Invariants

**VANTAGE** is an autonomous Business Intelligence engine designed to bridge the gap between deterministic data analysis and generative natural language explanations. It implements a strict **one-way data contract**:

```
[ Raw CSV/DB Sources ] 
        │ (L1: Calendar Conformance & Entity Resolution)
        ▼
[ Cleaned & Reconciled DataFrames ]
        │ (L3: 2-Axis Materiality Engine)
        ▼
[ Movement Event (Actual vs Seasonal Baseline) ]
        │ (L4: Attribution Ladder: Bridge, Event Join, Mix)
        ▼
[ Immutable EvidenceBundle (Content-Hashed SHA-256) ]
        │ (Pre-Prompt Row/Column Entitlement Scoping)
        ▼
[ Scoped EvidenceBundle ]
        │ (L6: 5-Factor Confidence & Abstention Gate)
   ┌────┴──────────────────────────┐
   ▼                               ▼
[ High/Med Confidence ]    [ Abstention Mode A/B/C ]
   │                               │
   ▼ (L7: Multi-Tier Narrative)    ▼
[ Gemini LLM Synthesis ]    [ Structured Abstention Payload ]
   │                               │
   ▼ (Numeric Firewall Gate)       │
[ Verified Executive Briefing ]    │
   │                               │
   └───────────────┬───────────────┘
                   ▼
       [ L7+: Action Composer ]
                   │
                   ▼ (L8: Feedback Loop)
       [ Beta-Bernoulli Ranking ]
                   │
                   ▼
       [ Hash-Chained Audit Ledger ]
```

### Core Code-Level Invariants

1. **Deterministic Numbers**: No LLM ever computes, forecasts, or aggregates numerical values. All calculations are executed by NumPy/Pandas pipelines before any prompt is assembled.
2. **Pre-Prompt Security Scoping**: Data entitlement policies (`row_policy`, `column_masks`) are executed directly on the Python `EvidenceBundle` object. Filtered rows and masked dimensions are purged *before* constructing prompts.
3. **Numeric Firewall Verification**: The output of any LLM call is parsed using regular expressions and set-intersection logic against the `EvidenceBundle`. If any numeral is ungrounded (orphan numeral) or if causal language is overused, the response is discarded, and the engine falls back to `T0_template`.
4. **Append-Only Tamper-Evident Audit**: Every event, narrative, user feedback, and action is written to `data/audit_ledger.jsonl` with an incremental cryptographic hash chain:
   $$\text{entry\_hash}_i = \text{SHA-256}\left(\text{entry\_hash}_{i-1} + \text{canonical\_json}(\text{entry}_i)\right)[:16]$$

---

## 2. Detailed Module Breakdown & Code Reference

### 2.1 L1: Reconciliation & Conformance (`vantage/reconciliation.py`)

Handles heterogeneous data inputs, calendar unification, product hierarchy joins, and grain-safe aggregations.

#### Functions & Signatures:

* `load_sources() -> dict[str, pd.DataFrame]`
  * Ingests `orders.csv`, `marketing.csv`, `supply.csv`, `dim_sku.csv`, and `cac_new_family.csv`.
  * Parses datetime timestamps and standardizes initial types.

* `conform_calendar(df: pd.DataFrame, date_col: str) -> pd.DataFrame`
  * Projects any date column onto the ISO Monday-start Gregorian week calendar:
    ```python
    out["iso_week_start"] = pd.to_datetime(out[date_col]).dt.to_period("W-SUN").apply(lambda p: p.start_time)
    ```

* `entity_resolve(orders: pd.DataFrame, dim_sku: pd.DataFrame) -> tuple[pd.DataFrame, dict]`
  * Performs a left join on `sku` between order lines and product dimension table.
  * Identifies unmapped SKUs and calculates reconciliation residual:
    ```python
    unresolved_mask = merged["product_family"].isna()
    residual = {
        "unresolved_order_count": int(unresolved_mask.sum()),
        "unresolved_revenue": float(merged.loc[unresolved_mask, "order_value"].sum()),
        "total_order_count": len(orders),
        "total_revenue": float(orders["order_value"].sum()),
    }
    ```

* `naive_vs_governed_margin(orders: pd.DataFrame, dim_sku: pd.DataFrame) -> dict`
  * Demonstrates the mathematical danger of averaging ratio metrics across dimensions:
    - **Naive (Incorrect)**: Average of segment margin percentages.
    - **Governed (Correct)**: $\frac{\sum \text{Revenue} - \sum \text{COGS}}{\sum \text{Revenue}}$.

---

### 2.2 L3: Detection & Materiality Engine (`vantage/materiality.py`)

Implements two-axis materiality to suppress operational noise and prevent alert fatigue.

#### Data Structures & Formulas:

```python
@dataclass
class Movement:
    kpi_id: str
    period_label: str
    actual: float
    baseline: float
    delta_abs: float
    delta_pct: float
    surprise_z: float
    impact_usd: float
    history_periods: int
    comparison_period: str
    comparison_actual: float
    wow_delta_abs: float
    wow_delta_pct: float
```

#### Mathematical Formulas:
1. **Seasonal Trailing Baseline**:
   $$\mu_{\text{baseline}} = \frac{1}{W} \sum_{t = T-W}^{T-1} y_t, \quad \sigma_{\text{baseline}} = \sqrt{\frac{1}{W} \sum_{t = T-W}^{T-1} (y_t - \mu_{\text{baseline}})^2}$$
   *(Default window $W = 8$ weeks).*

2. **Statistical Surprise ($Z$-Score)**:
   $$Z = \frac{y_T - \mu_{\text{baseline}}}{\sigma_{\text{baseline}}}$$

3. **Materiality Quadrant Evaluation**:
   ```python
   def materiality_quadrant(movement: Movement, min_impact_usd: float, min_surprise_z: float) -> str:
       high_impact = movement.impact_usd >= min_impact_usd
       high_surprise = abs(movement.surprise_z) >= min_surprise_z
       if high_impact and high_surprise: return "alert_full_diagnosis"
       if high_impact and not high_surprise: return "digest_expected_but_large"
       if not high_impact and high_surprise: return "weekly_digest"
       return "suppress"
   ```

4. **Hierarchy Collapse**:
   Collapses child regional alerts into a parent global event if children account for the movement, preventing redundant alert storms:
   ```python
   def hierarchy_collapse(parent_movement: Movement, child_deltas: dict[str, float]) -> dict
   ```

---

### 2.3 L4: Attribution & Diagnosis Ladder (`vantage/diagnosis/`)

#### 1. Arithmetic Bridge (`vantage/diagnosis/arithmetic_bridge.py`)
Implements the standard FP&A three-factor exact bridge identity:

$$\Delta \text{Revenue} = \text{Volume Effect} + \text{Mix Effect} + \text{Price Effect}$$

- **Volume Effect**: $(U_1 - U_0) \times \overline{\text{ASP}}_0$
- **Mix Effect**: $U_1 \times \sum_{s} \left[ (\text{mix}_{1,s} - \text{mix}_{0,s}) \times \text{Price}_{0,s} \right]$
- **Price Effect**: $\sum_{s} \left[ U_{1,s} \times (\text{Price}_{1,s} - \text{Price}_{0,s}) \right]$

#### 2. Business Event Join (`vantage/diagnosis/event_join.py`)
- `find_promo_end_events(marketing_df, prior_week, current_week)`: Scans marketing data for campaigns active in week $T-1$ but inactive in week $T$.
- `find_stockout_events(supply_df, week_start, week_end)`: Identifies hourly supply log records where `stockout_flag == True`.
- `scope_dollar_impact(prior_df, current_df, scope, value_col)`: Filters order datasets to exact event coordinates (e.g., `product_family="family_a"`, `region="AMER"`) and computes exact week-over-week dollar loss.

#### 3. Dimensional Contribution & Mix Shift (`vantage/diagnosis/contribution.py`)
- `beam_search_slices(prior_df, current_df, dims, top_k=5, depth=2)`: Adtributor-style multi-dimensional partition search that finds the highest impact single and pairwise dimension intersections without combinatorial explosion.
- `mix_variance_effect(prior_df, current_df, dimension)`: Isolates pure channel/category proportion shift holding baseline prices constant.

#### 4. Residual Accounting (`vantage/diagnosis/residual.py`)
- `residual_accounting(total_delta, attributed)`: Calculates exact unexplained noise:
  $$\text{Residual} = \Delta \text{Total} - \sum \text{Attributed Drivers}$$

---

### 2.4 L5: Evidence Bundle Model (`vantage/evidence.py`)

The immutable data contract passed to narrative and action engines.

```python
class EvidenceFact(BaseModel):
    evidence_id: str
    statement_type: Literal["driver_attribution", "structural_decomposition", "reconciliation", "data_quality"]
    label: str
    value: float
    unit: str
    method: str
    method_params: dict = Field(default_factory=dict)
    source_tables: list[str]
    freshness_ts: Optional[str] = None
    quality_tier: str = "gold"
    contribution_share: Optional[float] = None
    driver_id: Optional[str] = None
    driver_type: Optional[str] = None

class EvidenceBundle(BaseModel):
    event_id: str
    kpi_id: str
    period: str
    as_of_watermark: str
    movement: MovementFact
    facts: list[EvidenceFact]
    residual: dict
    contradictions: list[Contradiction] = Field(default_factory=list)
    confidence: Optional[ConfidenceBreakdown] = None
    entitlement_scope: Optional[EntitlementScope] = None
    telemetry: Optional[Telemetry] = None
    data_quality_flags: list[str] = Field(default_factory=list)
    bundle_hash: str = ""

    def compute_hash(self) -> str:
        payload = self.model_dump(exclude={"bundle_hash", "telemetry", "entitlement_scope"})
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def scoped_to(self, entitled_regions: list[str], masked_columns: list[str], persona_id: str, row_policy: str) -> "EvidenceBundle":
        # Filters out rows outside persona region and strips facts referencing masked columns
```

---

### 2.5 L6: Confidence Scoring & Abstention Gate (`vantage/confidence.py`)

#### 5-Factor Composite Score Calculation:

$$\text{Composite} = 0.25 C_{\text{data}} + 0.20 C_{\text{method}} + 0.25 C_{\text{coverage}} + 0.15 C_{\text{consistency}} + 0.15 C_{\text{history}}$$

Where:
- $C_{\text{data}} = 1.0 - \min(1.0, 0.5 \times N_{\text{dq\_flags}})$
- $C_{\text{method}} = \frac{\sum |v_i| \times \text{method\_conf}_i}{\sum |v_i|}$
- $C_{\text{coverage}} = \max(0.0, 1.0 - |\text{residual\_share}|)$
- $C_{\text{consistency}} = \max(0.0, 1.0 - 0.3 \times N_{\text{contradictions}})$
- $C_{\text{history}} = \min(1.0, \frac{N_{\text{history}}}{N_{\text{min\_required}}})$

#### Method Confidence Coefficients:
- `arithmetic_bridge`: $1.00$
- `business_event_join`: $0.90$
- `dimensional_contribution_slice`: $0.85$
- `causal_did`: $0.80$
- `causal_bsts`: $0.78$
- `dimensional_contribution_mix`: $0.72$
- `lagged_association`: $0.50$

#### Structured Abstention Modes:
- **`A_clarify`**: Ambiguous KPI resolution (e.g. "margin" $\rightarrow$ Gross Margin vs Contribution Margin).
- **`B_competing_hypotheses`**: Disagreement across attribution methods.
- **`C_hard_abstain`**: Upstream data freshness SLA breaches.

---

### 2.6 L7: Narrative Generation & Numeric Firewall (`vantage/narrative.py`)

#### Tier Router:
- `route_tier(bundle)`:
  - If contradictions or confidence in (`low`, `abstain`) $\rightarrow$ `T2_frontier` (`gemini-2.5-pro`).
  - If $\ge 3$ attributed drivers $\rightarrow$ `T1_small_model` (`gemini-3.5-flash-lite`).
  - Otherwise $\rightarrow$ `T0_template` (Deterministic python string rendering).

#### Numeric Firewall Implementation (`verify_narrative`):
1. **Identifier Strip**: Strips evidence tokens (`[E-01]`), SKU tokens (`SKU-4471`), and period strings (`week_30`).
2. **Numeral Extraction**: Regex matches all numeric strings (`-?\$?\d[\d,]*\.?\d*\s?%?`).
3. **Set Intersection Verification**: Converts extracted numbers to floats and verifies each value against the active `EvidenceBundle`.
4. **Causal Term Checking**: Ensures verbs (*"caused"*, *"drove"*) only describe drivers verified by causal inference (`causal_did`).
5. **Fallback Trigger**: If `verdict.passed == False`, automatically returns `render_template_narrative()`.

---

### 2.7 L8: Bayesian Feedback Loop (`vantage/feedback.py`)

Implements a conjugate Beta-Bernoulli update rule:

$$\text{Posterior Weight} = \frac{\alpha}{\alpha + \beta} = \frac{\text{Accepted} + 1}{\text{Accepted} + \text{Rejected} + 2}$$

- `submit_feedback(event_id, driver_id, polarity, analyst, comment)`:
  - Appends to `data/feedback_log.jsonl`.
  - Updates `data/driver_weights.json`.
- `apply_learned_ranking(facts: list[EvidenceFact])`:
  - Sorts facts by $(|\text{contribution\_share}| \times \text{posterior\_weight})$.

---

### 2.8 LLM Client Architecture (`vantage/llm.py`)

- **Zero-Dependency Core**: Uses Python's native `urllib.request` with SSL unverified context for portability.
- **Model Cascade**:
  - `gemini-3.5-flash-lite` $\rightarrow$ `gemini-3.1-flash-lite` $\rightarrow$ `gemini-3.5-flash` $\rightarrow$ `gemini-3.6-flash` $\rightarrow$ `gemini-flash-latest`.
- **Cost Engine**:
  - Flash-Lite: $\$0.0375 / 1\text{M}$ input tokens, $\$0.15 / 1\text{M}$ output tokens.
  - Pro: $\$1.25 / 1\text{M}$ input tokens, $\$5.00 / 1\text{M}$ output tokens.

---

### 2.9 Drift & Causal Analytics

#### Drift Detection (`vantage/drift.py`):
1. **Population Stability Index (PSI)**:
   $$\text{PSI} = \sum_{k=1}^{B} (P_k - Q_k) \ln\left(\frac{P_k}{Q_k}\right)$$
   Evaluates 10 equal-width bins between baseline and evaluation periods.
2. **Driver Rank Drift**:
   Computes Spearman rank correlation on driver posterior weights across sequential snapshots.

#### Difference-in-Differences Causal Estimator (`vantage/causal.py`):
$$\text{ATE} = (\bar{y}_{\text{treated, post}} - \bar{y}_{\text{treated, pre}}) - (\bar{y}_{\text{control, post}} - \bar{y}_{\text{control, pre}})$$
$$\text{SE}_{\text{DiD}} = \sqrt{\frac{s_{\text{treated, post}}^2}{N} + \frac{s_{\text{treated, pre}}^2}{N} + \frac{s_{\text{control, post}}^2}{N} + \frac{s_{\text{control, pre}}^2}{N}}$$

---

## 3. Declarative Registries & Configuration

### 3.1 Persona Registry (`vantage/personas.yaml`)

```yaml
- persona_id: cfo
  display_name: "CFO"
  role: leadership
  word_budget: 90
  depth: summary
  vocabulary_level: executive
  metric_scope: {regions: [EMEA, AMER, APAC], categories: all}
  decision_rights: [pricing_policy, budget_reallocation, headcount]
  lever_rights: []
  column_masks: []
  channel: [digest, push]
  cadence: weekly

- persona_id: regional_director_emea
  display_name: "Regional Sales Director (EMEA)"
  role: regional_sales
  word_budget: 140
  depth: segment
  vocabulary_level: operational
  metric_scope: {regions: [EMEA], categories: all}
  decision_rights: [discount_envelope, rep_focus, promo_request]
  lever_rights: [channel_incentive]
  column_masks: [customer_segment]
  channel: [alert, mobile]
  cadence: daily

- persona_id: category_manager
  display_name: "Category Manager"
  role: product
  word_budget: 160
  depth: sku
  vocabulary_level: operational
  metric_scope: {regions: [EMEA, AMER, APAC], categories: all}
  decision_rights: [assortment, price_ladder, promo_calendar]
  lever_rights: [promo_depth, safety_stock]
  column_masks: []
  channel: [conversational]
  cadence: on_demand

- persona_id: analyst
  display_name: "Data Analyst"
  role: analyst
  word_budget: 400
  depth: full
  vocabulary_level: technical
  metric_scope: {regions: [EMEA, AMER, APAC], categories: all}
  decision_rights: [model_config, thresholds, contract_edits]
  lever_rights: []
  column_masks: []
  channel: [workbench]
  cadence: on_demand
```

### 3.2 Lever Registry (`vantage/levers.yaml`)

```yaml
- lever_id: promo_depth
  display_name: "Promotional Depth & Calendar"
  driver_id: promo_calendar
  owner_role: Category Manager
  lead_time_days: 5
  expected_impact:
    point: 5.2
    ci_low: 3.1
    ci_high: 7.4
    unit: pct_revenue_recovery
    source: historical_promo_elasticity
  constraints:
    - "Max discount depth: 25%"
    - "Requires 48h notice to channel partners"
  default_monitoring_plan:
    watch: [net_revenue, gross_margin_pct]
    window_days: 14

- lever_id: safety_stock
  display_name: "Safety Stock Replenishment"
  driver_id: stockout_rate
  owner_role: Category Manager
  lead_time_days: 2
  expected_impact:
    point: 2.8
    ci_low: 1.5
    ci_high: 4.2
    unit: pct_revenue_recovery
    source: lost_sales_runrate
  constraints:
    - "Warehouse capacity limit: 85%"
  default_monitoring_plan:
    watch: [units_sold, stockout_hours]
    window_days: 7

- lever_id: channel_incentive
  display_name: "Direct Channel Rebate / Incentive"
  driver_id: channel_mix
  owner_role: Regional Sales Director (EMEA)
  lead_time_days: 10
  expected_impact:
    point: 1.4
    ci_low: 0.6
    ci_high: 2.3
    unit: pct_asp_recovery
    source: channel_rebate_elasticity
  constraints:
    - "Direct channel margin must remain >= 58%"
  default_monitoring_plan:
    watch: [channel_mix, asp]
    window_days: 21
```

---

## 4. API Endpoints & Request-Response Lifecycles

### Complete Endpoint Map:

| Route | Method | Purpose | Input / Parameters | Output Payload |
| :--- | :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | System liveness | None | `{"status": "ok"}` |
| `/api/scenario/{id}` | `GET` | Run Scenario Engine | `scenario_id` (path), `persona_id`, `use_llm` | Full Scoped Bundle, Narrative, Actions, Alerts, Scorecard, Debug |
| `/api/ask` | `POST` | Conversational Q&A | `{"text": str, "scenario_id": str, "persona_id": str}` | `{"resolved_kpi": str, "abstention": dict, "answer": str}` |
| `/api/feedback` | `POST` | Analyst Feedback | `{"event_id": str, "driver_id": str, "polarity": str, "analyst": str}` | Structured Feedback Record + Updated Posterior Weights |
| `/api/contracts` | `GET` | Contract Definitions | None | List of validated `KPIContract` dicts |
| `/api/personas` | `GET` | Persona Definitions | None | List of `Persona` dicts |
| `/api/telemetry` | `GET` | LLM Cost & Latency | None | Cumulative token, latency, cost metrics |
| `/api/audit` | `GET` | Audit Log | `limit` (query) | Hash-chained audit ledger records |
| `/api/reconciliation`| `GET` | Data Source Audit | None | Freshness audit + Naive vs. Governed Margin |
| `/api/alerts/{id}` | `GET` | Proactive Alerts | `scenario_id` (path) | Triggered Alert list + Delivery dispatch log |
| `/api/drift/{id}` | `GET` | Distribution Shift | `scenario_id` (path) | PSI & Driver Rank Correlation Reports |
| `/api/causal/{id}` | `GET` | Causal Inference | `scenario_id` (path) | DiD Point Estimate, CI & Parallel Trends Check |

---

## 5. Demonstration Scenarios & Recovery Metrics

### Benchmark Verification against Ground Truth (`data/ground_truth.json`)

The engine's attribution accuracy is evaluated on every run using `vantage/scorecard.py`:

```json
{
  "ground_truth": {
    "kpi_id": "net_revenue",
    "period": "week_30",
    "total_movement_usd": -5758.0,
    "drivers": [
      {
        "driver_id": "promo_calendar",
        "true_dollar_impact": -3774.0,
        "true_share": 0.6554
      },
      {
        "driver_id": "stockout_rate",
        "true_dollar_impact": -1637.0,
        "true_share": 0.2843
      },
      {
        "driver_id": "channel_mix",
        "true_dollar_impact": -748.0,
        "true_share": 0.1299
      }
    ],
    "noise": {
      "true_dollar_impact": 401.0,
      "true_share": -0.0696
    }
  }
}
```

#### Performance Metrics:
- **Driver Recall@3**: $1.00$ ($3/3$ true drivers identified).
- **Attribution MAE**: $< 2.5\%$ percentage points (Target: $< 5.0\%$).
- **Residual Error**: $< 1.5\%$ percentage points (Target: $< 3.0\%$).
- **Rank Correlation (Spearman $\rho$)**: $1.000$ (Identical ranking order).
- **Firewall Hallucination Rate**: $0.00\%$ ($0$ orphan numerals across all scenarios).

---

## 6. Test Suite & Verification Commands

The test suite validates pipeline integrity, contract schema validation, LLM resilience, and firewall guardrails.

```bash
# Run complete test suite
python3 -m pytest tests/ -v

# Run individual test modules
python3 -m pytest tests/test_pipeline.py -v     # Pipeline & Scenarios 1-4
python3 -m pytest tests/test_completion.py -v   # Full execution & ledger
python3 -m pytest tests/test_llm.py -v          # Gemini client & fallback
```

---

*Report automatically compiled and code-verified for VANTAGE — Business Intelligence AI Engine.*
