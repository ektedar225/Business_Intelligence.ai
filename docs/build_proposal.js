const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, AlignmentType, PageBreak, LevelFormat,
  Header, Footer, PageNumber, TabStopType, TabStopPosition,
} = require("docx");
const fs = require("fs");

const NAVY = "1B2A4A";
const ACCENT = "2F5DA6";
const ACCENT2 = "1F8A6E";
const MUTED = "5B6472";
const LIGHT = "EEF2F8";
const WARN = "B5560E";

const FONT = "Calibri";
const MONO = "Consolas";

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160 },
    border: { bottom: { color: ACCENT, space: 4, style: BorderStyle.SINGLE, size: 6 } },
    children: [new TextRun({ text, bold: true, color: NAVY, size: 30 })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, bold: true, color: ACCENT, size: 24 })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, color: NAVY, size: 21 })],
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    children: [new TextRun({ text, size: 21, font: FONT, ...opts })],
  });
}
function pRuns(runs, opts = {}) {
  return new Paragraph({ spacing: { after: 160, line: 276 }, ...opts, children: runs });
}
function bullet(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 90 },
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, size: 21, font: FONT, ...opts })],
  });
}
function callout(text, color = ACCENT2) {
  return new Paragraph({
    spacing: { before: 120, after: 200 },
    border: {
      left: { color, space: 8, style: BorderStyle.SINGLE, size: 18 },
    },
    shading: { type: ShadingType.CLEAR, fill: LIGHT },
    indent: { left: 100 },
    children: [new TextRun({ text, italics: true, size: 21, font: FONT, color: NAVY })],
  });
}
function mono(text) {
  return new Paragraph({
    spacing: { after: 160 },
    shading: { type: ShadingType.CLEAR, fill: "1E2430" },
    children: text.split("\n").map((line, i) =>
      new TextRun({ text: line, font: MONO, size: 18, color: "D7E2F0", break: i === 0 ? 0 : 1 })
    ),
  });
}

function cell(text, opts = {}) {
  const { width, bold = false, color = "000000", fill = null, align = AlignmentType.LEFT, size = 19 } = opts;
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: fill ? { type: ShadingType.CLEAR, fill } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text: String(text), bold, color, size, font: FONT })],
    })],
  });
}

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((hdr, i) => cell(hdr, { width: widths[i], bold: true, color: "FFFFFF", fill: NAVY, size: 18 })),
  });
  const bodyRows = rows.map((r, ri) =>
    new TableRow({
      children: r.map((val, i) => cell(val, { width: widths[i], fill: ri % 2 === 1 ? LIGHT : null })),
    })
  );
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headerRow, ...bodyRows],
  });
}

function coverTitle() {
  return [
    new Paragraph({ spacing: { before: 1800, after: 0 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "VANTAGE", bold: true, size: 72, color: NAVY, font: FONT })] }),
    new Paragraph({ spacing: { after: 240 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "KPI Intelligence-to-Action Engine", size: 30, color: ACCENT, font: FONT })] }),
    new Paragraph({ spacing: { after: 600 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Detailed Business Proposal", size: 24, italics: true, color: MUTED, font: FONT })] }),
    new Paragraph({ spacing: { after: 60 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Accenture Innovation Challenge 2026 — Round 2", size: 20, color: MUTED, font: FONT })] }),
    new Paragraph({ spacing: { after: 900 }, alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Problem Track 3 — BusinessIntelligence.ai", size: 20, color: MUTED, font: FONT })] }),
    new Paragraph({ spacing: { after: 100 }, alignment: AlignmentType.CENTER,
      border: { top: { color: ACCENT, space: 10, style: BorderStyle.SINGLE, size: 8 } },
      children: [new TextRun({ text: "\"The LLM never touches a number. Every figure in every narrative is a", italics: true, size: 22, color: NAVY, font: FONT })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
      children: [new TextRun({ text: "pointer to a deterministically computed, lineage-traced evidence object —", italics: true, size: 22, color: NAVY, font: FONT })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 700 },
      children: [new TextRun({ text: "and a verifier proves it before delivery.\"", italics: true, size: 22, color: NAVY, font: FONT })] }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

const children = [];
children.push(...coverTitle());

// ---------- 1. Executive Summary ----------
children.push(h1("1. Executive Summary"));
children.push(p("Most enterprise “KPI storytelling” tools follow the same pattern: SQL pulls a number, an LLM writes a paragraph around it. That approach fails the central requirement of this brief — the LLM must not be the source of quantitative truth — because the moment a model is asked to narrate a number, it can also invent one, and nothing downstream can tell the difference."));
children.push(p("VANTAGE is architected so that a hallucinated figure is structurally impossible to ship, not merely discouraged by a prompt. Every quantity in every delivered narrative is a citation into an immutable, content-hashed Evidence Bundle that is assembled entirely by deterministic code — arithmetic, statistics, and rule-based reconciliation — before any language model ever sees the data. A numeric firewall then re-derives every number in the generated text and rejects the response if any figure cannot be traced back to that bundle."));
children.push(callout("Positioning: VANTAGE is a governed analytical engine with a generative interface. Deterministic core, generative shell."));
children.push(p("This document covers the full solution design, and reports real, measured results from a working prototype built against it: a multi-factor revenue movement with three independently injected causes was diagnosed with 3-of-3 driver recall, perfect rank agreement against ground truth, and 0.46 percentage points of attribution error — figures the prototype computed, not figures asserted for this proposal.", { bold: false }));
children.push(h3("Headline results from the working prototype"));
children.push(table(
  ["Claim", "Measured result"],
  [
    ["Driver recall @ 3 (injected drivers found)", "3 / 3"],
    ["Rank correlation vs. ground truth (Spearman ρ)", "1.0"],
    ["Attribution error (mean abs. error on contribution share)", "0.46 pp (target < 5 pp)"],
    ["Residual accuracy (reported vs. true unexplained share)", "1.38 pp (target < 3 pp)"],
    ["Numeric-firewall violations shipped", "0 (a live fabrication-injection test was caught: see §5.4)"],
    ["Governance gap caught (naive vs. grain-safe margin %)", "1.8 pp on real region-level data (see §3.1)"],
    ["Share of narrative generation requiring a model call", "0% — 100% deterministic template tier in this build"],
  ],
  [6300, 3700]
));

// ---------- 2. Problem Framing ----------
children.push(h1("2. Problem Framing"));
children.push(h2("2.1 What actually breaks in enterprises today"));
children.push(table(
  ["Observed failure", "Root cause", "What VANTAGE does instead"],
  [
    ["“Revenue is down 8%” — nobody knows why for days", "Diagnosis is manual SQL archaeology", "Automated driver decomposition + business-event join, seconds not days"],
    ["Analysts drown in alerts", "Materiality = one threshold on one metric", "Two-axis materiality (surprise × impact) + hierarchy collapse"],
    ["Two teams quote different “revenue”", "No governed KPI contract", "Versioned KPI contracts as the single source of definition"],
    ["LLM copilots quietly invent figures", "The LLM is asked to compute", "Numeric firewall + causal-language gate; the model never touches a table"],
    ["Insight arrives, nothing changes", "No link to levers or owners", "Actions are drawn from a Lever Registry: owner, expected impact, monitoring plan"],
    ["Nobody can say if the system works", "No feedback capture", "Recommendation-to-outcome tracking + a Bayesian driver-ranking feedback loop"],
  ],
  [3200, 3000, 3800]
));

children.push(h2("2.2 Target personas"));
children.push(p("Personas are a design primitive here, not a UI theme: each one gets a different depth of narrative, a different set of levers it is allowed to pull, and a different slice of the evidence — enforced mechanically, described in §5.3."));
children.push(table(
  ["Persona", "Question they ask", "Decision rights (levers)", "Depth / cadence"],
  [
    ["CFO / Leadership", "“Are we going to miss the quarter, and what's the one thing that matters?”", "Budget reallocation, pricing policy, headcount", "3-sentence summary, weekly digest"],
    ["Regional Sales Director", "“Why is my region soft and what can I do this week?”", "Channel incentive / discount envelope, rep focus", "Segment detail, daily alert"],
    ["Category Manager", "“Is it price, mix, or supply?”", "Promo calendar, safety stock, assortment", "SKU-level detail, on-demand"],
    ["Data Analyst", "“Show me the method and the evidence.”", "Model config, thresholds, contract edits", "Full method log, workbench"],
  ],
  [2200, 3200, 2600, 2000]
));

// ---------- 3. Solution Architecture ----------
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("3. Solution Architecture"));
children.push(p("The system is a nine-layer pipeline. Layers L0–L5 are entirely deterministic — ingestion, reconciliation, materiality detection, and diagnosis never call a model. L6 is a rule-based confidence gate. Only L7, narrative synthesis, is generative, and even there the model receives nothing but the finished evidence bundle: no database connection, no raw tables, no ability to compute or fetch a figure of its own."));
children.push(table(
  ["Layer", "Responsibility", "LLM involved?"],
  [
    ["L0 Ingestion", "Heterogeneous sources at different grains and cadences", "No"],
    ["L1 Reconciliation & Conformance", "Calendar conformance, entity resolution, freshness watermarking, grain-safe aggregation", "No"],
    ["L2 Semantic & Governance", "Versioned KPI contracts: definitions, driver DAG, materiality thresholds, entitlements", "No"],
    ["L3 Detection / Materiality", "Baseline forecast, surprise score, two-axis materiality, hierarchy collapse", "No"],
    ["L4 Diagnosis Engine", "Arithmetic bridge, dimensional contribution, business-event join, residual accounting", "No"],
    ["L5 Evidence Bundle", "Immutable, typed, content-hashed contract between the deterministic core and the model", "No"],
    ["L6 Confidence & Abstention", "Five-component confidence score, banding, three abstention behaviours", "No (rule-based)"],
    ["L7 Narrative + Action", "Persona narrative, numeric firewall, causal-language gate, action composer", "Yes — bounded, verified"],
    ["L8 Delivery & Feedback", "Digest / alert / conversational surfaces; feedback capture and re-ranking", "No"],
  ],
  [2400, 5300, 1900]
));
children.push(callout("One evidence engine, two surfaces: a proactive digest and a conversational “ask VANTAGE” entry point both terminate in the same L3–L7 pipeline and the same Evidence Bundle — this is what keeps the two experiences consistent rather than being two disconnected demos.", ACCENT));

children.push(h2("3.1 L1 — Reconciliation & Conformance, and why it matters"));
children.push(p("The brief stresses different refresh cadences, grains, and quality levels across sources. Four mechanisms address this: calendar conformance (all sources projected onto one enterprise calendar so week-over-week comparisons never silently mix periods), as-of watermarking (every fact carries the freshness of its slowest contributing source; a source that has breached its SLA marks the affected driver UNVERIFIABLE rather than being computed on stale data), entity resolution (a conformed SKU/product dimension; unmapped rows accumulate into a reported residual rather than disappearing), and grain-safe aggregation (a ratio metric such as ASP or margin % is always recomputed from summed numerator and denominator — never averaged across regions)."));
children.push(p("That last rule is not academic. In the prototype's own data, naively averaging Gross Margin % across three regions reports 31.41%. Recomputing it correctly from summed revenue and summed cost — the grain-safe way — reports 33.21%. Same data; a 1.8 percentage-point difference caused entirely by one region (APAC) carrying materially higher landed cost on a smaller revenue base. An unweighted average overweights it; a governed recompute does not.", {}));
children.push(table(
  ["Region", "Margin % (region-level, correctly computed)"],
  [["AMER", "43.69%"], ["APAC", "9.15%"], ["EMEA", "41.39%"]],
  [5000, 5000]
));
children.push(callout("Naive average of the three region percentages: 31.41%.  Governed recompute from summed components: 33.21%.  Gap: −1.8 pp — measured on the prototype's own data, not a hypothetical.", WARN));

children.push(h2("3.2 L2 — KPI Semantic Contracts"));
children.push(p("Every KPI is a versioned YAML artifact, validated on load, that is simultaneously the definition store, the driver graph, the materiality configuration, the lineage record, and the security policy. Adding a KPI becomes a config commit, not an engineering project — the direct answer to “how does this generalize.” The prototype ships five contracts (Net Revenue, Units Sold, ASP, Gross Margin %, CAC) spanning three sources of different grain and cadence. An abbreviated example:"));
children.push(mono(
`kpi_id: net_revenue
formula: "SUM(gross_amount) - SUM(returns_amount) - SUM(discount_amount)"
grain: {entity: order_line, time: day}
additivity: additive
hierarchy: {decomposition: "units * asp"}
registered_drivers:
  - {id: promo_calendar, type: controllable, lever: promo_depth}
  - {id: stockout_rate,  type: controllable, lever: safety_stock}
  - {id: channel_mix,    type: controllable, lever: channel_incentive}
materiality: {min_business_impact_usd: 3000, min_surprise_z: 1.5}
entitlements:
  row_policy: "region_in(user.regions)"
  column_masks: {customer_segment: "hash_if_not(role='analyst')"}`
));

children.push(h2("3.3 L3 — Detection: materiality is two axes, not one"));
children.push(table(
  ["", "Low business impact", "High business impact"],
  [
    ["Low statistical surprise", "Suppress (log only)", "Digest — “expected, but large”"],
    ["High statistical surprise", "Weekly digest", "Alert + full diagnosis"],
  ],
  [2600, 3700, 3700]
));
children.push(p("Surprise is scored against a trailing-window forecast baseline — not a naive period-over-period comparison — which is what stops the engine firing on every expected seasonal swing. In the prototype run, this distinction is visible directly: the raw week-over-week change in Net Revenue was −8.69%, while the same movement scored against an 8-week forecast baseline came out to a surprise z-score of −2.21 against a smaller baseline-relative delta of −6.33% — two different, both legitimate, numbers answering two different questions (“what changed since last week” vs. “was this surprising against trend”), and the system keeps them separate rather than collapsing them into one figure."));
children.push(p("Hierarchy collapse then prevents an alert storm: a global Net Revenue movement and its regional children (in the live run: AMER −65.6% of the move, EMEA −33.1%, APAC −1.3%) are reported as one event, with the regions attached as evidence rather than fired as three separate alerts."));

children.push(h2("3.4 L4 — Diagnosis Engine: the method ladder"));
children.push(p("Analyzers run cheapest-and-most-certain first. This ordering is the direct, demonstrable answer to the brief's central question — when to use deterministic logic vs. statistics vs. causal inference vs. an LLM, and why."));
children.push(table(
  ["#", "Method", "Certainty", "Used for, in this build"],
  [
    ["1", "Arithmetic bridge (volume / mix / price)", "Exact — algebra, sums to the total by construction", "Company-wide structural decomposition of the revenue move"],
    ["2", "Dimensional contribution (slice search + mix-variance)", "Exact for a slice; a defensible estimate for compositional mix", "Finding the hot-spot slices, and isolating the channel-mix effect"],
    ["3", "Business-event join", "High — near-free once the event exists in S2/S3", "Promo-end and stockout events, joined on time window + scope"],
    ["4–5", "Lagged association / causal inference (DiD, BSTS)", "Correlational / causal-under-assumptions", "Designed for; not exercised in this prototype build (see §6)"],
    ["6", "LLM hypothesis proposal & narrative", "Zero quantitative authority", "Proposes which of 1–5 to run; writes the prose only"],
  ],
  [500, 2700, 2700, 3100]
));
children.push(p("Residual accounting is a first-class output at every step, not an afterthought: after event-join attributes the promo-end and stockout effects and mix-variance attributes the channel-mix effect, whatever remains is reported honestly as unexplained — in the live run, −7.0% of the movement, against a true injected-noise share of −8.4%."));

children.push(h2("3.5 L5 — The Evidence Bundle"));
children.push(p("An immutable, typed, SHA-256-hashed object is the sole interface between the deterministic core and the generative layer. It carries the movement, every attributed fact (value, method, source tables, freshness, quality tier, contribution share), the residual, any contradictions, the confidence breakdown, and the entitlement scope already applied. The rule enforced in code: the narrative service receives only this object. It has no database connection. It cannot fetch a number even if a prompt tried to make it."));

children.push(h2("3.6 L6 — Confidence & three distinct abstention behaviours"));
children.push(table(
  ["Component", "Measures", "Weight"],
  [
    ["Data", "Freshness vs. SLA, data-quality flags", "25%"],
    ["Method", "Strength of the methods used (exact bridge = 1.0; correlation-only = 0.5)", "20%"],
    ["Coverage", "1 − |unexplained residual share|", "25%"],
    ["Consistency", "Agreement between independent methods; penalized per contradiction", "15%"],
    ["History", "Periods available vs. the contract's required minimum", "15%"],
  ],
  [2200, 5400, 2400]
));
children.push(p("Abstention is treated as a shipped feature, not a failure path — each mode states what is missing and what would resolve it:"));
children.push(table(
  ["Mode", "Trigger", "Demonstrated in the prototype as"],
  [
    ["A — Clarify", "A business term maps to more than one registered KPI", "Asking “how is performance this week” resolves to a clarifying question between Net Revenue and Gross Margin %"],
    ["B — Competing hypotheses", "Independent methods disagree with no dominant driver", "Designed for; not exercised as a live scenario in this build"],
    ["C — Hard abstain", "A required source has breached its freshness SLA", "Gross Margin % is blocked when the supply/cost feed is 26h stale against a 6h SLA — confidence is hard-capped and the revenue-side facts (unaffected by that feed) are still surfaced as reliable"],
  ],
  [1800, 3600, 3600]
));

children.push(h2("3.7 L7 — Narrative, the numeric firewall, and the action composer"));
children.push(p("Generation in this build is template-based (Tier T0): the narrative service does not call a model to produce its default output at all, which is the strongest possible demonstration that the LLM contributes zero numbers — it is architecturally absent from the money path, not merely well-behaved. A complexity-based tier router is implemented and evaluated on every bundle (it would escalate to a small or frontier model for higher-driver-count or lower-confidence cases), but no model call was exercised in this prototype build; see §6 for the honest accounting of what that implies."));
children.push(p("Three verification gates run regardless of which tier produced the text:"));
children.push(bullet("Numeric firewall — every numeral in the rendered text is extracted and must match a value in the Evidence Bundle within a magnitude-scaled tolerance; an unmatched numeral is a hard fail."));
children.push(bullet("Causal-language gate — verbs such as “caused” or “drove” are only permitted on a sentence that cites a fact produced by a causal_* method; everything else must read as association or coincidence."));
children.push(bullet("(Designed for, not exercised without a model call in this build) an LLM faithfulness critic that checks entailment between the bundle and the text."));
children.push(callout("Live test performed in the prototype: a passing CFO narrative was deliberately corrupted with an appended sentence — “This was primarily caused by a 3.4% swing in competitor pricing in the region” — citing a fabricated evidence id. The firewall rejected it, flagging the orphan numeral 0.034 with zero false positives on the genuine narrative. This is the fifteen-second stage demo the brief's central instruction calls for.", ACCENT2));
children.push(p("Actions are drawn from a Lever Registry and filtered by the persona's actual decision rights — never invented, and a material driver the persona cannot act on becomes a named escalation instead of a fabricated sense of agency. In the live run: the CFO persona escalates all three drivers (no operational lever is in that persona's rights in this registry); the Regional Sales Director can pull the channel-incentive lever (expected impact 1.8%, CI 0.5–3.0, from the registry, not computed by the narrative); the Category Manager can pull promo-depth and safety-stock."));

children.push(h2("3.8 L8 — Delivery, audit, and the feedback loop"));
children.push(p("Every delivered insight is written to an append-only, hash-chained audit ledger recording the persona, the bundle hash, the methods run, the model version (or “template”), and any feedback — chained so a retroactive edit to the ledger is detectable. A working feedback loop lets an analyst accept or reject a specific driver; rejections update a Bayesian posterior weight per driver that measurably demotes it in future rankings — demonstrated live by rejecting a driver four times and watching it drop below a lower-magnitude driver it previously outranked."));

// ---------- 4. Security ----------
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("4. Security, Entitlements & Auditability"));
children.push(p("The governing design decision: entitlements are enforced on the Evidence Bundle, before the prompt is built — never by asking a model to redact. A prompt-level instruction to hide data is not a security control, because it can be argued with, forgotten under complexity, or bypassed by a sufficiently adversarial input; a row that was never placed in the bundle cannot be leaked by anything downstream."));
children.push(p("This is not asserted — it is mechanically demonstrated in the prototype. The same Net Revenue movement, viewed by two personas:"));
children.push(table(
  ["", "CFO", "Regional Sales Director (EMEA)"],
  [
    ["Facts visible", "All drivers, all regions", "Region-scoped: the AMER-only promo-end fact is absent from the bundle entirely"],
    ["Column-level detail", "Full access (no mask declared)", "customer_segment is masked; the narrative states the limitation rather than silently omitting it"],
    ["Actions offered", "0 actions, 3 escalations (no operational lever in this persona's rights)", "1 action (channel-incentive), 1 escalation"],
  ],
  [1800, 3700, 3700]
));

// ---------- 5. Prototype ----------
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("5. The Working Prototype: What Was Built and Measured"));
children.push(p("This section reports what the Round 2 prototype actually contains and what it actually measured — as distinct from the architecture proposed above, and honest about the gap between the two (§6)."));

children.push(h2("5.1 Data: three deliberately mismatched sources"));
children.push(table(
  ["Source", "Grain", "Cadence", "Latency / quality"],
  [
    ["S1 Orders", "order_line × day", "Continuous", "Gold"],
    ["S2 Marketing", "campaign × product_family × week", "Weekly", "Silver, 48h latency"],
    ["S3 Supply / Inventory", "sku × warehouse × hour", "Hourly", "Bronze, 24h latency (and deliberately breached to 26h vs. a 6h SLA for the abstention scenario)"],
  ],
  [2400, 3200, 1800, 2200]
));
children.push(p("Five connected KPIs span these sources: Net Revenue, Units Sold, and ASP (S1 only); Gross Margin % (S1 + S3); CAC (S1 + S2, weekly grain, deliberately sparse for a newly launched product line)."));

children.push(h2("5.2 Scenario 1 — the multi-factor movement, with ground truth injected"));
children.push(p("The data generator injects three independent, known causes into a week-over-week Net Revenue drop, then the diagnosis engine is run completely blind to those injected values. The comparison is the Recovery Scorecard — the single highest-leverage piece of evidence in this proposal, because it turns “our engine sounds convincing” into “we measured whether it is right.”"));
children.push(table(
  ["Injected driver", "True share", "Diagnosed share", "True $", "Diagnosed $"],
  [
    ["Promo campaign ended (SKU-1001, AMER)", "65.5%", "65.5%", "−$3,774", "−$3,774"],
    ["SKU-4471 stockout, DE warehouse (EMEA)", "28.4%", "28.4%", "−$1,637", "−$1,637"],
    ["Channel mix shift toward marketplace", "14.4%", "13.0%", "−$828", "−$748"],
    ["Noise / unattributable", "−8.4%", "−7.0%", "—", "—"],
  ],
  [3200, 1600, 1700, 1600, 1500]
));
children.push(callout("Driver recall@3: 3/3.  Spearman rank correlation vs. true ranking: 1.0.  Mean absolute attribution error: 0.46 percentage points (target < 5).  Residual error: 1.38 percentage points (target < 3). The two exactly-matching drivers (promo, stockout) are exact partition sums via business-event-join; the channel-mix figure is a mix-variance estimate, honestly a few tenths of a point off — the scorecard reports that gap rather than hiding it.", ACCENT2));
children.push(p("The resulting CFO-persona narrative, rendered entirely by the template engine and passed by the firewall on the first attempt:"));
children.push(mono(
`Net Revenue fell 8.7% WoW ($-5,758)

Net Revenue fell to $60,467 in week_30, down $5,758 (-8.7%) from
$66,225 in week_29.

- Promo campaign CMP-family_a-AMER ended (AMER) coincided with
  $-3,774 (65.5% of the movement) [E-01]
- SKU-4471 stockout in DE warehouse (EMEA) coincided with
  $-1,637 (28.4% of the movement) [E-02]

What we don't know: 7.0% of the movement is unattributed residual.

Confidence: HIGH (composite 0.85) - based on 31% of the required
history, 93% of the movement explained.`
));

children.push(h2("5.3 Scenario 2 — abstention on a stale source"));
children.push(p("The S3 supply/cost feed is deliberately generated to be 26 hours stale against a contract-declared 6-hour freshness SLA for the current week. Gross Margin % cannot be safely computed, and the system abstains — mode C, hard abstain — rather than silently computing on partial data:"));
children.push(mono(
`[ABSTAIN - C_hard_abstain]

Net Revenue for week 30 is $60,467, fully verified and unaffected by
the supply feed - only the cost side of the margin calculation is
blocked.

Blocker: S3 supply/cost feed for gross_margin_pct is 26h stale
against a 6h freshness SLA.
Why it matters: Computing this KPI on stale cost data would silently
corrupt the answer rather than degrade it visibly.
Resolution: Refresh the S3 supply/cost feed; the affected driver
will automatically re-verify once the SLA is met. (owner: data-ops)`
));
children.push(p("Confidence composite is hard-capped at 0.30 (band: ABSTAIN) regardless of the other four components — a deliberate design choice: a single hard data-quality breach overrides an otherwise-healthy score."));

children.push(h2("5.4 Scenario 3 — sparse history"));
children.push(p("CAC for a product family launched three weeks before the analysis date is evaluated against a contract that requires 26 periods of history for the statistical baseline. The system disables that baseline, falls back to a stated plan-vs-actual comparison, and hard-caps confidence at Low (composite 0.649) with the limitation stated in the narrative rather than a false-precision forecast."));

children.push(h2("5.5 LLM vs. non-LLM: the determinism accounting"));
children.push(p("Per-insight telemetry recorded for every scenario in this build: 0 model calls, $0.00 cost, 100% of narratives produced by the deterministic template tier. This is a more conservative (and more honestly demonstrable) claim than the architecture's target split of roughly 92% deterministic / 8% model-assisted — in this prototype, the model-assisted tier is implemented as a routing decision (evaluated and logged for every bundle) but not exercised, so that the headline claim — the LLM contributes zero numbers — holds with zero exceptions rather than “almost always.”"));

// ---------- 6. Honest gap accounting ----------
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("6. Technology Stack, and an Honest Gap Accounting"));
children.push(p("The brief asks teams to distinguish native, configured, custom-built, and externally integrated capabilities. The table below does that for what was actually built in Round 2, against what the full design proposes for a production deployment."));
children.push(table(
  ["Layer", "Round 2 prototype (built)", "Production-mapped design", "Build type"],
  [
    ["Storage", "In-memory pandas / CSV", "Snowflake / Databricks / Fabric", "Native (swap-in)"],
    ["Semantic contracts", "YAML + Pydantic validation", "Same, or dbt Semantic Layer / Cube", "Custom"],
    ["Diagnosis engine", "Custom Python (bridge, contribution, event-join)", "Same, + DoWhy/EconML for causal rungs", "Custom"],
    ["Orchestration", "Direct function calls (vantage/pipeline.py)", "Prefect / Dagster", "Custom → Integrated"],
    ["LLM orchestration", "Template engine (T0); tier router implemented, unexercised", "LangGraph state machine + Claude", "Custom → Integrated"],
    ["API / Frontend", "FastAPI + vanilla HTML/JS dashboard", "Same + embedded BI extension", "Custom"],
    ["Entitlements", "In-process row/column filtering on the bundle", "Postgres RLS / Snowflake row-access policies", "Custom → Configured"],
    ["Audit ledger", "Hash-chained append-only JSONL", "Immutable store / Delta with CDF", "Custom"],
    ["Telemetry", "In-bundle timing + tier-routing log", "Langfuse + OpenTelemetry", "Custom → Integrated"],
  ],
  [1800, 3000, 2600, 1600]
));
children.push(h2("6.1 What is not built, stated plainly"));
children.push(bullet("Causal inference (DiD / synthetic control / BSTS) — method rungs 4–5 on the ladder are designed for (the Evidence Bundle already carries a causal_* method namespace and the narrative gate already enforces causal-language rules against it) but not implemented; every causal claim in the current build is correctly downgraded to associative language as a result."));
children.push(bullet("Abstention mode B (competing hypotheses) — modes A and C are both live; B is designed but not wired to a scenario."));
children.push(bullet("A real model call for the T1/T2 narrative tiers — the routing decision is real and logged; the actual generation always falls through to the template, by deliberate choice, to keep the headline determinism claim exceptionless."));
children.push(bullet("Production-grade infrastructure (dbt lineage tests, Prefect scheduling, Postgres RLS, Langfuse tracing, a vector store for contextual retrieval) — each is architecturally accounted for above and is a swap-in at a named integration point, not a redesign."));
children.push(p("Stating these gaps is itself part of the pitch: the brief explicitly rewards teams who show judgment about when to use which method and why, and a prototype that quietly overclaimed causal inference would undercut the exact discipline the numeric firewall exists to enforce."));

// ---------- 7. Business case ----------
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("7. Business Case & Impact"));
children.push(p("All figures below are illustrative assumptions for a mid-size enterprise, stated explicitly per the brief's guidance, not derived from the synthetic prototype data."));
children.push(h2("7.1 Cost"));
children.push(bullet("Infrastructure + orchestration: roughly $2–4k/month at ~50k insights/month in a production deployment."));
children.push(bullet("LLM cost at the design's target tier mix (55% template / 35% small model / 10% frontier): roughly $0.011 blended per insight, ~$550/month at that volume — versus $0 in the current prototype, which runs 100% on the template tier."));
children.push(bullet("Build: roughly 3 engineers × 4 months to a production pilot, following the phased roadmap below."));
children.push(h2("7.2 Value (illustrative: 40 analysts, ~$100k loaded cost each)"));
children.push(bullet("~30% of analyst time is ad-hoc “why did X change” diagnosis (~$1.2M/yr of effort); a 50% reduction is ~$600k/yr of recovered capacity, redeployed to forward-looking work rather than headcount reduction."));
children.push(bullet("Decision latency from ~3 days to minutes: on a $500M revenue base, catching a 1% margin leak four days earlier is roughly $55k per incident; at 12 incidents/year, ~$660k/yr."));
children.push(bullet("Avoided wrong decisions from ungoverned or hallucinated figures — low frequency, high severity; treated as risk-adjusted upside, not a headline number."));
children.push(callout("Honest framing: the provable, year-one component of ROI is time-to-insight and action-outcome tracking, both of which this prototype's audit ledger and feedback loop are built to measure directly — not the larger, harder-to-isolate avoided-risk figure.", ACCENT));

// ---------- 8. Roadmap ----------
children.push(h1("8. Phased Roadmap"));
children.push(table(
  ["Phase", "Scope", "Exit criterion", "Status"],
  [
    ["0 · Contract foundation", "KPI contracts, source conformance, audit ledger", "Two teams agree on one revenue definition", "Delivered in this prototype (5 contracts, 3 sources)"],
    ["1 · Detect & explain", "Materiality engine, arithmetic/contribution/event-join analyzers, template-only narrative", "Driver recall@3 ≥ 0.8 on backtest", "Delivered — measured recall@3 = 3/3"],
    ["2 · Narrate & govern", "Model-assisted narrative tier, numeric firewall + critic, personas, entitlements", "Zero orphan numerals over 1,000 generations", "Firewall + entitlements delivered; model tier designed, not exercised"],
    ["3 · Act & learn", "Lever registry, action composer, feedback write-backs, outcome tracking", "30% action-acceptance rate", "Action composer + feedback loop delivered; outcome tracking not yet measured"],
    ["4 · Causal & scale", "DiD/BSTS/DML analyzers, 25+ KPIs, second domain, self-serve onboarding", "New KPI live in < 1 day, config-only", "Not started — highest-value next step"],
  ],
  [1900, 3000, 2600, 2500]
));
children.push(p("The sequencing is deliberate and was followed in this build: the deterministic engine (Phases 0–1) was built and measured before any narrative or model-tier work (Phase 2), which is both the correct engineering order and the strongest available signal that quantitative correctness was never delegated to a language model."));

// ---------- 9. Risks ----------
children.push(h1("9. Key Risks & Mitigations"));
children.push(table(
  ["Risk", "Mitigation"],
  [
    ["Hallucinated numbers destroy trust on day one", "Numeric firewall + causal-language gate + zero-orphan target, demonstrated live against an injected fabrication"],
    ["Spurious drivers from mass correlation testing", "Pre-registered driver DAG (a driver must exist in the KPI contract); residual is always reported, never hidden"],
    ["Alert fatigue kills adoption", "Two-axis materiality + hierarchy collapse; alerts/day is a tracked metric"],
    ["Semantic drift as contracts age", "Versioned contracts, one owner per KPI, schema validation on load (the prototype fails to start on an invalid contract)"],
    ["Analysts see it as a threat, not a tool", "Positioned as a diagnosis accelerator; the feedback loop gives analysts direct, measurable authority over driver ranking"],
    ["Causal claims wrong under bad assumptions", "Causal language is mechanically gated to causal_* methods only; every other driver is stated as associative"],
    ["LLM cost sprawl at scale", "Tiered routing + semantic caching design; this prototype demonstrates the $0 floor of that spectrum directly"],
    ["Entitlement leak via prompt manipulation", "Filtering happens on the bundle before the prompt exists — demonstrated: the Regional Director's bundle never contains the AMER-only fact, regardless of what any prompt asks for"],
  ],
  [3600, 6400]
));

// ---------- 10. Appendix ----------
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("10. Appendix: Selected Artifacts"));
children.push(h2("10.1 Lever registry entry (used by the Action Composer, never invented at generation time)"));
children.push(mono(
`lever_id: channel_incentive
driver_id: channel_mix
owner_role: regional_sales
lead_time_days: 14
expected_impact: {point: 1.8, ci_low: 0.5, ci_high: 3.0,
                   unit: pct_revenue_recovery, source: elasticity_model}
constraints: ["incentive budget capped at $30k/quarter per region"]
default_monitoring_plan:
  watch_metrics: [asp, channel_mix]
  window_days: 30
  success_threshold: "direct-channel share back above 60%"
  rollback_trigger: "no shift after 30 days"`
));
children.push(h2("10.2 Persona registry entry"));
children.push(mono(
`persona_id: regional_director_emea
role: regional_sales
depth: segment
metric_scope: {regions: [EMEA], categories: all}
lever_rights: [channel_incentive]
column_masks: [customer_segment]
cadence: daily`
));
children.push(h2("10.3 Repository layout"));
children.push(bullet("vantage/contracts/*.yaml — the five KPI contracts"));
children.push(bullet("vantage/{reconciliation,materiality,diagnosis/*,evidence,confidence,narrative,actions,scorecard,audit,feedback}.py — the deterministic core, each module independently testable"));
children.push(bullet("api/main.py + api/static/index.html — the FastAPI service and browser dashboard used for every result in §5"));
children.push(bullet("tests/test_pipeline.py — automated checks pinning the recovery-scorecard targets, firewall pass/fail behaviour, entitlement filtering, and abstention triggers"));
children.push(bullet("scripts/run_demo.py — headless one-command reproduction of every number in this document"));

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 420, hanging: 260 } } } }],
    }],
  },
  styles: {
    default: {
      document: { run: { font: FONT, size: 21 } },
    },
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          border: { bottom: { color: "C9D2E0", space: 4, style: BorderStyle.SINGLE, size: 4 } },
          children: [
            new TextRun({ text: "VANTAGE — Business Proposal", size: 16, color: MUTED, font: FONT }),
            new TextRun({ text: "\tAccenture Innovation Challenge 2026 · Round 2 · Track 3", size: 16, color: MUTED, font: FONT }),
          ],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Page ", size: 16, color: MUTED, font: FONT }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: MUTED, font: FONT }),
            new TextRun({ text: " of ", size: 16, color: MUTED, font: FONT }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: MUTED, font: FONT }),
          ],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(__dirname + "/../VANTAGE_Business_Proposal.docx", buf);
  console.log("Written VANTAGE_Business_Proposal.docx", buf.length, "bytes");
});
