const pptxgen = require("pptxgenjs");

const NAVY = "1B2A4A";
const NAVY2 = "24365E";
const LIGHT = "F5F7FB";
const ICE = "D7E4F7";
const ICE_TXT = "AFC6EC";
const MINT = "1F8A6E";
const CORAL = "C0392B";
const MUTED = "5B6472";
const WHITE = "FFFFFF";

const FONT = "Calibri";
const HEAD = "Cambria";

function newDeck() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
  pres.author = "VANTAGE";
  pres.company = "Accenture Innovation Challenge 2026";
  return pres;
}

function circleIcon(slide, x, y, glyph, opts = {}) {
  const size = opts.size || 0.55;
  slide.addShape("ellipse", {
    x, y, w: size, h: size,
    fill: { color: opts.fill || MINT },
    line: { type: "none" },
  });
  slide.addText(glyph, {
    x, y, w: size, h: size,
    align: "center", valign: "middle",
    fontFace: FONT, fontSize: opts.fontSize || 20, bold: true,
    color: opts.color || WHITE,
  });
}

function pageNum(slide, n) {
  slide.addText(String(n), {
    x: 12.6, y: 7.05, w: 0.5, h: 0.3, fontSize: 10, color: MUTED, align: "right", fontFace: FONT,
  });
}

function contentSlide(pres, title, kicker) {
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  if (kicker) {
    slide.addText(kicker.toUpperCase(), {
      x: 0.6, y: 0.4, w: 10, h: 0.35, fontSize: 12, bold: true, color: MINT, charSpacing: 2, fontFace: FONT,
    });
  }
  slide.addText(title, {
    x: 0.6, y: kicker ? 0.72 : 0.5, w: 12.1, h: 0.9, fontSize: 30, bold: true, color: NAVY, fontFace: HEAD,
  });
  return slide;
}

function statCard(slide, x, y, w, h, value, label, opts = {}) {
  slide.addShape("roundRect", {
    x, y, w, h, rectRadius: 0.08,
    fill: { color: opts.fill || LIGHT },
    line: { type: "none" },
    shadow: { type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 },
  });
  slide.addText(value, {
    x, y: y + h * 0.14, w, h: h * 0.5, align: "center", valign: "middle",
    fontSize: opts.valueSize || 34, bold: true, color: opts.valueColor || NAVY, fontFace: HEAD,
  });
  slide.addText(label, {
    x: x + 0.1, y: y + h * 0.62, w: w - 0.2, h: h * 0.35, align: "center", valign: "top",
    fontSize: opts.labelSize || 12, color: MUTED, fontFace: FONT,
  });
}

const pres = newDeck();

// ============ 1. TITLE ============
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addShape("ellipse", { x: 10.6, y: -2.2, w: 6, h: 6, fill: { color: NAVY2 }, line: { type: "none" } });
  s.addShape("ellipse", { x: -2.4, y: 5.2, w: 4.5, h: 4.5, fill: { color: NAVY2 }, line: { type: "none" } });
  s.addText("ACCENTURE INNOVATION CHALLENGE 2026  ·  ROUND 2  ·  TRACK 3 — BUSINESSINTELLIGENCE.AI", {
    x: 0.9, y: 0.7, w: 11.5, h: 0.4, fontSize: 12, color: ICE_TXT, charSpacing: 1.5, fontFace: FONT, bold: true,
  });
  s.addText("VANTAGE", {
    x: 0.85, y: 2.5, w: 11.5, h: 1.6, fontSize: 72, bold: true, color: WHITE, fontFace: HEAD,
  });
  s.addText("The KPI Intelligence-to-Action Engine", {
    x: 0.9, y: 3.95, w: 11, h: 0.6, fontSize: 24, color: ICE, fontFace: FONT,
  });
  s.addText("The LLM never touches a number.", {
    x: 0.9, y: 5.7, w: 10, h: 0.5, fontSize: 20, italics: true, color: WHITE, fontFace: HEAD,
  });
  s.addText("Every figure is a pointer to a deterministically computed, lineage-traced evidence object — verified before delivery.", {
    x: 0.9, y: 6.2, w: 10.5, h: 0.5, fontSize: 13, color: ICE_TXT, fontFace: FONT,
  });
}

// ============ 2. THE PROBLEM ============
{
  const s = contentSlide(pres, "Most KPI copilots are one hallucination away from disaster", "The problem");
  const items = [
    ["3 days", "to find out why revenue moved — manual SQL archaeology, every time"],
    ["40+ alerts/week", "because materiality is one threshold on one metric, so analysts stop reading"],
    ["1 wrong number", "is all it takes: an LLM asked to compute a KPI can also invent one, silently"],
  ];
  const cardW = 3.85, gap = 0.35, startX = 0.6, y = 1.9;
  items.forEach((it, i) => {
    const x = startX + i * (cardW + gap);
    s.addShape("roundRect", { x, y, w: cardW, h: 3.0, rectRadius: 0.08, fill: { color: LIGHT }, line: { type: "none" } });
    circleIcon(s, x + 0.35, y + 0.35, "!", { fill: i === 2 ? CORAL : NAVY });
    s.addText(it[0], { x: x + 0.35, y: y + 1.1, w: cardW - 0.7, h: 0.7, fontSize: 26, bold: true, color: NAVY, fontFace: HEAD });
    s.addText(it[1], { x: x + 0.35, y: y + 1.8, w: cardW - 0.7, h: 1.0, fontSize: 13.5, color: MUTED, fontFace: FONT });
  });
  s.addText("The brief's instruction is precise: the LLM should not be treated as the source of quantitative truth. Most teams will build “SQL → LLM → nice paragraph.” That fails it.", {
    x: 0.6, y: 5.25, w: 12.1, h: 1.2, fontSize: 15, italics: true, color: NAVY, fontFace: FONT,
  });
  pageNum(s, 2);
}

// ============ 3. THE THESIS ============
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("THE THESIS", { x: 0.9, y: 0.9, w: 6, h: 0.4, fontSize: 13, bold: true, color: MINT, charSpacing: 2, fontFace: FONT });
  s.addText("Deterministic core. Generative shell.", {
    x: 0.85, y: 1.5, w: 11.5, h: 1.2, fontSize: 40, bold: true, color: WHITE, fontFace: HEAD,
  });
  s.addText("VANTAGE is a governed analytical engine with a generative interface — not a chatbot with a database plugged in.", {
    x: 0.9, y: 2.75, w: 10.8, h: 0.7, fontSize: 17, color: ICE, fontFace: FONT,
  });
  const rows = [
    ["Arithmetic, statistics, and rule-based reconciliation", "compute every number — L0 through L6, zero model calls"],
    ["An immutable, content-hashed Evidence Bundle", "is the only thing the model ever sees — no database, no raw tables"],
    ["A numeric firewall + causal-language gate", "re-derives every figure in the generated text and rejects orphans"],
  ];
  let y = 3.75;
  rows.forEach((r) => {
    circleIcon(s, 0.9, y, "✓", { fill: MINT, size: 0.42, fontSize: 16 });
    s.addText([{ text: r[0] + "  ", options: { bold: true, color: WHITE } }, { text: r[1], options: { color: ICE_TXT } }], {
      x: 1.5, y: y - 0.08, w: 10.8, h: 0.55, fontSize: 15, fontFace: FONT, valign: "middle",
    });
    y += 0.72;
  });
  pageNum(s, 3);
}

// ============ 4. ARCHITECTURE ============
{
  const s = contentSlide(pres, "Nine layers; the model speaks only through one gate", "Architecture");
  const layers = [
    ["L0-L1", "Ingestion & Reconciliation", "Calendar conformance, entity resolution, freshness watermarking"],
    ["L2", "Semantic Governance", "Versioned KPI contracts: definitions, driver DAG, entitlements"],
    ["L3", "Detection & Materiality", "Forecast baseline, two-axis materiality, hierarchy collapse"],
    ["L4", "Diagnosis Engine", "Arithmetic bridge, contribution, business-event join, residuals"],
    ["L5", "Evidence Bundle", "Immutable, typed, hashed — the only thing the model can see"],
    ["L6", "Confidence & Abstention", "5-component score; clarify / hard-abstain / competing hypotheses"],
    ["L7", "Narrative + Firewall", "Persona prose, numeric firewall, causal gate, action composer"],
    ["L8", "Delivery & Feedback", "Digest, alert, conversational — one engine, every surface"],
  ];
  const colW = 5.95, rowH = 0.95, gapX = 0.3;
  layers.forEach((l, i) => {
    const col = i < 4 ? 0 : 1;
    const row = i % 4;
    const x = 0.6 + col * (colW + gapX);
    const y = 1.85 + row * (rowH + 0.18);
    const isModel = l[0] === "L7";
    s.addShape("roundRect", { x, y, w: colW, h: rowH, rectRadius: 0.06, fill: { color: isModel ? "2A4A3C" : LIGHT }, line: { type: "none" } });
    s.addShape("roundRect", { x: x + 0.12, y: y + rowH / 2 - 0.19, w: 0.62, h: 0.38, rectRadius: 0.06, fill: { color: isModel ? MINT : NAVY }, line: { type: "none" } });
    s.addText(l[0], { x: x + 0.12, y: y + rowH / 2 - 0.19, w: 0.62, h: 0.38, align: "center", valign: "middle", fontSize: 12, bold: true, color: WHITE, fontFace: FONT });
    s.addText(l[1], { x: x + 0.9, y: y + 0.14, w: colW - 1.05, h: 0.34, fontSize: 14.5, bold: true, color: isModel ? WHITE : NAVY, fontFace: FONT });
    s.addText(l[2], { x: x + 0.9, y: y + 0.48, w: colW - 1.05, h: 0.4, fontSize: 11, color: isModel ? ICE : MUTED, fontFace: FONT });
  });
  s.addText("Only L7 is generative — and even there, the model has no database connection.", {
    x: 0.6, y: 6.95, w: 12, h: 0.35, fontSize: 12, italics: true, color: MUTED, fontFace: FONT,
  });
  pageNum(s, 4);
}

// ============ 5. METHOD LADDER ============
{
  const s = contentSlide(pres, "Cheapest and most certain method runs first", "The diagnosis ladder");
  const rows = [
    ["1", "Arithmetic bridge", "Exact — algebra, not inference", MINT],
    ["2", "Dimensional contribution", "Exact for a slice; estimated for compositional mix", MINT],
    ["3", "Business-event join", "High — near-free once the event exists", MINT],
    ["4-5", "Lagged association / causal inference", "Correlational, or causal under stated assumptions", "8C6D1F"],
    ["6", "LLM hypothesis + narrative", "Zero quantitative authority — proposes tests, writes prose", NAVY],
  ];
  let y = 1.95;
  rows.forEach((r) => {
    s.addShape("roundRect", { x: 0.6, y, w: 12.1, h: 0.85, rectRadius: 0.06, fill: { color: LIGHT }, line: { type: "none" } });
    circleIcon(s, 0.85, y + 0.15, r[0], { fill: r[3], size: 0.55, fontSize: 15 });
    s.addText(r[1], { x: 1.65, y: y + 0.08, w: 4.3, h: 0.35, fontSize: 15, bold: true, color: NAVY, fontFace: FONT });
    s.addText(r[2], { x: 1.65, y: y + 0.42, w: 10.8, h: 0.35, fontSize: 12, color: MUTED, fontFace: FONT });
    y += 1.0;
  });
  pageNum(s, 5);
}

// ============ 6. DEMO NARRATIVE ============
{
  const s = contentSlide(pres, "One evidence bundle, rendered for the CFO", "Live in the prototype");
  s.addShape("roundRect", { x: 0.6, y: 1.85, w: 7.6, h: 4.7, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
  const lines = [
    "Net Revenue fell 8.7% WoW ($-5,758)",
    "",
    "Net Revenue fell to $60,467 in week_30, down $5,758",
    "(-8.7%) from $66,225 in week_29.",
    "",
    "- Promo campaign ended (AMER) coincided with",
    "  $-3,774 (65.5% of the movement)  [E-01]",
    "- SKU-4471 stockout in DE warehouse (EMEA)",
    "  coincided with $-1,637 (28.4%)  [E-02]",
    "",
    "What we don't know: 7.0% of the movement is",
    "unattributed residual.",
    "",
    "Confidence: HIGH (composite 0.85)",
  ];
  s.addText(lines.join("\n"), {
    x: 0.9, y: 2.1, w: 7.0, h: 4.2, fontSize: 12.5, color: ICE, fontFace: "Courier New", lineSpacing: 17,
  });
  const notes = [
    ["Every [E-id] is clickable", "and opens the exact method, source table, freshness, and contribution share behind that number."],
    ["Every causal-sounding word is gated", "“coincided with”, not “caused by” — this fact came from business-event-join, not a causal method."],
    ["Rendered by a template", "— tier T0, zero model calls, $0.00 — and still passed the numeric firewall on the first attempt."],
  ];
  let ny = 1.95;
  notes.forEach((n) => {
    circleIcon(s, 8.5, ny, "→", { fill: MINT, size: 0.4, fontSize: 15 });
    s.addText([{ text: n[0] + " ", options: { bold: true, color: NAVY } }, { text: n[1], options: { color: MUTED } }], {
      x: 9.05, y: ny - 0.08, w: 3.65, h: 1.3, fontSize: 12, fontFace: FONT,
    });
    ny += 1.55;
  });
  pageNum(s, 6);
}

// ============ 7. RECOVERY SCORECARD ============
{
  const s = contentSlide(pres, "We didn't just build a convincing engine. We measured it.", "The recovery scorecard");
  s.addText("Three drivers were injected into the synthetic data with known dollar impact. The diagnosis engine ran completely blind to those values.", {
    x: 0.6, y: 1.5, w: 12.1, h: 0.5, fontSize: 13, color: MUTED, fontFace: FONT,
  });
  const stats = [
    ["3 / 3", "Driver recall @ 3"],
    ["1.0", "Rank correlation (Spearman ρ)"],
    ["0.46 pp", "Attribution error (target < 5pp)"],
    ["1.38 pp", "Residual error (target < 3pp)"],
  ];
  const cw = 2.9, gap = 0.15;
  stats.forEach((st, i) => statCard(s, 0.6 + i * (cw + gap), 2.15, cw, 1.7, st[0], st[1], { valueColor: MINT }));

  s.addChart(pres.ChartType.bar, [
    {
      name: "True %",
      labels: ["Promo ended", "Stockout", "Channel mix"],
      values: [65.5, 28.4, 14.4],
    },
    {
      name: "Diagnosed %",
      labels: ["Promo ended", "Stockout", "Channel mix"],
      values: [65.5, 28.4, 13.0],
    },
  ], {
    x: 0.6, y: 4.1, w: 12.1, h: 2.8,
    barDir: "col", barGapWidthPct: 40,
    chartColors: [NAVY, MINT],
    showTitle: true, title: "True vs. diagnosed contribution share", titleFontSize: 13, titleColor: NAVY,
    showLegend: true, legendPos: "b", legendFontSize: 10,
    showValue: true, dataLabelFontSize: 9, dataLabelColor: MUTED, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0",
    catAxisLabelColor: MUTED, catAxisLabelFontSize: 11,
    valAxisLabelColor: MUTED, valAxisLabelFontSize: 10, valAxisTitle: "% of movement",
    valGridLine: { color: "E3E8F0", size: 1 }, catGridLine: { style: "none" },
  });
  pageNum(s, 7);
}

// ============ 8. FIREWALL DEMO ============
{
  const s = contentSlide(pres, "The fifteen-second demo the brief asks for", "Numeric firewall, live");
  const colW = 5.95;
  // Clean
  s.addShape("roundRect", { x: 0.6, y: 1.85, w: colW, h: 4.6, rectRadius: 0.08, fill: { color: LIGHT }, line: { type: "none" } });
  s.addText("GENUINE NARRATIVE", { x: 0.9, y: 2.05, w: 5, h: 0.3, fontSize: 11, bold: true, color: MUTED, charSpacing: 1.5, fontFace: FONT });
  s.addText("“...Confidence: HIGH (composite 0.85) — based on\n31% of the required history, 93% of the\nmovement explained.”", {
    x: 0.9, y: 2.4, w: colW - 0.6, h: 1.6, fontSize: 12.5, italics: true, color: NAVY, fontFace: FONT,
  });
  circleIcon(s, 0.9, 4.3, "✓", { fill: MINT, size: 0.5, fontSize: 18 });
  s.addText("PASSED — 0 orphan numerals, 0 causal overreach", { x: 1.55, y: 4.35, w: 4.7, h: 0.4, fontSize: 13, bold: true, color: MINT, fontFace: FONT });

  // Corrupted
  s.addShape("roundRect", { x: 0.6 + colW + 0.3, y: 1.85, w: colW, h: 4.6, rectRadius: 0.08, fill: { color: LIGHT }, line: { type: "none" } });
  s.addText("SAME TEXT, ONE SENTENCE INJECTED", { x: 0.9 + colW + 0.3, y: 2.05, w: 5, h: 0.3, fontSize: 11, bold: true, color: MUTED, charSpacing: 1.5, fontFace: FONT });
  s.addText("“...This was primarily caused by a 3.4% swing\nin competitor pricing in the region. [E-99]”", {
    x: 0.9 + colW + 0.3, y: 2.4, w: colW - 0.6, h: 1.6, fontSize: 12.5, italics: true, color: CORAL, fontFace: FONT,
  });
  circleIcon(s, 0.9 + colW + 0.3, 4.3, "✗", { fill: CORAL, size: 0.5, fontSize: 18 });
  s.addText("CAUGHT — orphan numeral 0.034, no matching evidence", { x: 1.55 + colW + 0.3, y: 4.35, w: 4.9, h: 0.4, fontSize: 13, bold: true, color: CORAL, fontFace: FONT });

  s.addText("E-99 does not exist in the Evidence Bundle. The number 3.4% matches nothing the deterministic core ever computed. The firewall does not ask the model to be careful — it checks.", {
    x: 0.6, y: 6.55, w: 12.1, h: 0.6, fontSize: 12.5, italics: true, color: MUTED, fontFace: FONT,
  });
  pageNum(s, 8);
}

// ============ 9. PERSONAS + ENTITLEMENTS ============
{
  const s = contentSlide(pres, "Same event, two personas — enforced before the prompt exists", "Security & personas");
  const colW = 5.95;
  const cols = [
    ["CFO", NAVY, [
      ["Facts visible", "All drivers, all regions"],
      ["Column detail", "Full access"],
      ["Actions", "0 actions, 3 escalations — no operational lever in this persona's rights"],
    ]],
    ["Regional Sales Director (EMEA)", MINT, [
      ["Facts visible", "Region-scoped — the AMER-only fact is absent from the bundle entirely"],
      ["Column detail", "customer_segment masked; narrative states the limitation"],
      ["Actions", "1 action (channel-incentive, 1.8% impact), 1 escalation"],
    ]],
  ];
  cols.forEach((c, i) => {
    const x = 0.6 + i * (colW + 0.3);
    s.addShape("roundRect", { x, y: 1.85, w: colW, h: 4.7, rectRadius: 0.08, fill: { color: LIGHT }, line: { type: "none" } });
    s.addShape("roundRect", { x: x + 0.25, y: 2.1, w: colW - 0.5, h: 0.5, rectRadius: 0.06, fill: { color: c[1] }, line: { type: "none" } });
    s.addText(c[0], { x: x + 0.25, y: 2.1, w: colW - 0.5, h: 0.5, align: "center", valign: "middle", fontSize: 15, bold: true, color: WHITE, fontFace: FONT });
    let ry = 2.85;
    c[2].forEach((row) => {
      s.addText(row[0].toUpperCase(), { x: x + 0.3, y: ry, w: colW - 0.6, h: 0.3, fontSize: 10.5, bold: true, color: MUTED, charSpacing: 1, fontFace: FONT });
      s.addText(row[1], { x: x + 0.3, y: ry + 0.3, w: colW - 0.6, h: 0.85, fontSize: 12.5, color: NAVY, fontFace: FONT });
      ry += 1.2;
    });
  });
  s.addText("Row policy: region_in(user.regions)  ·  enforced on the Evidence Bundle itself, before any prompt is built.", {
    x: 0.6, y: 6.75, w: 12.1, h: 0.35, fontSize: 12, italics: true, color: MUTED, fontFace: FONT,
  });
  pageNum(s, 9);
}

// ============ 10. ABSTENTION ============
{
  const s = contentSlide(pres, "Abstaining well is a feature, not a failure", "Confidence & abstention");
  const modes = [
    ["A — Clarify", MINT, "“how is performance this week?” resolves to: “'performance' could mean gross_margin_pct or net_revenue — which one did you mean?”"],
    ["C — Hard abstain", CORAL, "S3 supply/cost feed is 26h stale against a 6h SLA. Gross Margin % is blocked — but Net Revenue, unaffected by that feed, is still shown as reliable."],
    ["Sparse history", "8C6D1F", "A 3-week-old product line's CAC falls back to plan-vs-actual; confidence hard-capped at LOW (0.649) with the limitation stated, not hidden."],
  ];
  let y = 1.95;
  modes.forEach((m) => {
    s.addShape("roundRect", { x: 0.6, y, w: 12.1, h: 1.45, rectRadius: 0.08, fill: { color: LIGHT }, line: { type: "none" } });
    s.addShape("roundRect", { x: 0.85, y: y + 0.25, w: 2.3, h: 0.5, rectRadius: 0.25, fill: { color: m[1] }, line: { type: "none" } });
    s.addText(m[0], { x: 0.85, y: y + 0.25, w: 2.3, h: 0.5, align: "center", valign: "middle", fontSize: 12.5, bold: true, color: WHITE, fontFace: FONT });
    s.addText(m[2], { x: 3.4, y: y + 0.15, w: 9.05, h: 1.15, fontSize: 13, color: NAVY, fontFace: FONT, valign: "middle" });
    y += 1.65;
  });
  pageNum(s, 10);
}

// ============ 11. ACTIONS ============
{
  const s = contentSlide(pres, "Actions are drawn from a registry — never invented", "Driver → lever → action → impact");
  const steps = ["Driver", "Controllable lever", "Action", "Expected impact", "Owner", "Monitoring plan"];
  const stepW = 1.85, stepGap = 0.15;
  steps.forEach((st, i) => {
    const x = 0.6 + i * (stepW + stepGap);
    s.addShape("roundRect", { x, y: 1.9, w: stepW, h: 0.75, rectRadius: 0.06, fill: { color: i === 3 ? MINT : NAVY }, line: { type: "none" } });
    s.addText(st, { x, y: 1.9, w: stepW, h: 0.75, align: "center", valign: "middle", fontSize: 11.5, bold: true, color: WHITE, fontFace: FONT });
    if (i < steps.length - 1) {
      s.addText("→", { x: x + stepW, y: 1.9, w: stepGap + 0.05, h: 0.75, align: "center", valign: "middle", fontSize: 16, color: MUTED, fontFace: FONT });
    }
  });
  s.addText("Worked example from the live run", { x: 0.6, y: 3.0, w: 8, h: 0.35, fontSize: 13, bold: true, color: NAVY, fontFace: FONT });
  const example = [
    ["channel_mix", "channel_incentive", "Fund a direct-channel incentive to rebalance mix away from marketplace"],
    ["expected impact", "1.8%  (CI 0.5–3.0)", "copied verbatim from the lever registry — never computed by the narrative"],
    ["owner / lead time", "regional_sales / 14 days", "monitoring plan: watch asp + channel_mix for 30 days"],
  ];
  let y = 3.5;
  example.forEach((r) => {
    s.addText([{ text: r[0] + "   ", options: { bold: true, color: MINT } }, { text: r[1] + "   ", options: { bold: true, color: NAVY } }, { text: r[2], options: { color: MUTED } }], {
      x: 0.6, y, w: 12.1, h: 0.5, fontSize: 13, fontFace: FONT,
    });
    y += 0.55;
  });
  s.addText("A driver a persona cannot act on becomes a named escalation — never a fabricated sense of agency. In the live run, the CFO persona escalates all three drivers in Scenario 1.", {
    x: 0.6, y: 5.6, w: 12.1, h: 0.8, fontSize: 13, italics: true, color: MUTED, fontFace: FONT,
  });
  pageNum(s, 11);
}

// ============ 12. DETERMINISM & COST ============
{
  const s = contentSlide(pres, "The determinism accounting, on a single slide", "LLM vs. non-LLM");
  const stats = [
    ["100%", "of narratives from the deterministic template tier"],
    ["0", "model calls across every scenario in this build"],
    ["$0.00", "cost per insight, measured, not estimated"],
    ["0", "numeric-firewall violations shipped"],
  ];
  const cw = 2.9, gap = 0.15;
  stats.forEach((st, i) => statCard(s, 0.6 + i * (cw + gap), 1.95, cw, 1.9, st[0], st[1], { valueColor: i === 2 ? MINT : NAVY, valueSize: 32 }));
  s.addText("The model performs exactly two bounded jobs in this architecture: parsing intent, and writing prose from a bundle it cannot alter. A tier router (T0 / T1 / T2) is implemented and evaluated on every bundle for cost/latency planning — this build renders 100% of narratives on T0, by choice, to keep the headline claim exceptionless rather than “almost always true.”", {
    x: 0.6, y: 4.2, w: 12.1, h: 1.6, fontSize: 14, color: NAVY, fontFace: FONT,
  });
  s.addText("Full design targets ~92% deterministic compute at scale, with T1/T2 model tiers for higher-complexity cases — see the Business Proposal for the tier-routing economics.", {
    x: 0.6, y: 6.0, w: 12.1, h: 0.6, fontSize: 12, italics: true, color: MUTED, fontFace: FONT,
  });
  pageNum(s, 12);
}

// ============ 13. GOVERNANCE MOMENT ============
{
  const s = contentSlide(pres, "Same data. One answer is wrong.", "The governance moment");
  s.addText("Naively averaging Gross Margin % across three regions vs. recomputing it from summed revenue and summed cost — on the prototype's own generated data:", {
    x: 0.6, y: 1.55, w: 12.1, h: 0.55, fontSize: 13, color: MUTED, fontFace: FONT,
  });
  s.addChart(pres.ChartType.bar, [
    { name: "Margin %", labels: ["AMER", "APAC", "EMEA"], values: [43.69, 9.15, 41.39] },
  ], {
    x: 0.6, y: 2.2, w: 6.9, h: 3.3,
    barDir: "col", chartColors: [NAVY],
    showTitle: true, title: "Region-level margin % (correctly computed)", titleFontSize: 12, titleColor: NAVY,
    showLegend: false, showValue: true, dataLabelFontSize: 10, dataLabelColor: MUTED, dataLabelPosition: "outEnd",
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valGridLine: { color: "E3E8F0", size: 1 }, catGridLine: { style: "none" },
  });
  statCard(s, 7.85, 2.2, 4.85, 1.5, "31.41%", "Naive average of the three region %s  —  WRONG", { valueColor: CORAL, valueSize: 30 });
  statCard(s, 7.85, 3.9, 4.85, 1.5, "33.21%", "Governed recompute from summed components  —  RIGHT", { valueColor: MINT, valueSize: 30 });
  s.addText("Gap: −1.8 percentage points — caused entirely by APAC's higher landed cost on a smaller revenue base. An unweighted average overweights it; a governed recompute does not.", {
    x: 7.85, y: 5.55, w: 4.85, h: 1.0, fontSize: 11.5, italics: true, color: MUTED, fontFace: FONT,
  });
  pageNum(s, 13);
}

// ============ 14. ROADMAP ============
{
  const s = contentSlide(pres, "The engine was built before the narrative, on purpose", "Phased roadmap");
  const phases = [
    ["0", "Contract foundation", "DELIVERED", MINT],
    ["1", "Detect & explain", "DELIVERED — recall@3 = 3/3", MINT],
    ["2", "Narrate & govern", "FIREWALL LIVE — model tier designed", "8C6D1F"],
    ["3", "Act & learn", "COMPOSER + FEEDBACK LIVE", "8C6D1F"],
    ["4", "Causal & scale", "NEXT", MUTED],
  ];
  const w = 2.28, gap = 0.15;
  phases.forEach((ph, i) => {
    const x = 0.6 + i * (w + gap);
    s.addShape("roundRect", { x, y: 2.2, w, h: 3.6, rectRadius: 0.08, fill: { color: LIGHT }, line: { type: "none" } });
    circleIcon(s, x + w / 2 - 0.28, 2.5, ph[0], { fill: NAVY, size: 0.56, fontSize: 18 });
    s.addText(ph[1], { x: x + 0.1, y: 3.25, w: w - 0.2, h: 0.7, align: "center", fontSize: 13.5, bold: true, color: NAVY, fontFace: FONT });
    s.addShape("roundRect", { x: x + 0.15, y: 4.5, w: w - 0.3, h: 0.9, rectRadius: 0.15, fill: { color: ph[3] }, line: { type: "none" } });
    s.addText(ph[2], { x: x + 0.2, y: 4.5, w: w - 0.4, h: 0.9, align: "center", valign: "middle", fontSize: 10.5, bold: true, color: WHITE, fontFace: FONT });
  });
  s.addText("The deterministic engine (Phases 0–1) was built and measured before any generative work — the correct engineering order, and the strongest signal that quantitative correctness was never delegated to a model.", {
    x: 0.6, y: 6.1, w: 12.1, h: 0.7, fontSize: 13, italics: true, color: MUTED, fontFace: FONT,
  });
  pageNum(s, 14);
}

// ============ 15. BUSINESS CASE ============
{
  const s = contentSlide(pres, "Illustrative, for a 40-analyst enterprise", "Business case");
  const stats = [
    ["~$600k/yr", "recovered analyst capacity at 50% less time on ad-hoc diagnosis"],
    ["3 days → minutes", "decision latency — ~$660k/yr from catching margin leaks earlier"],
    ["~$0.011", "blended cost per insight at target tier mix (55% template / 35% small / 10% frontier)"],
  ];
  const cw = 3.85, gap = 0.35;
  stats.forEach((st, i) => statCard(s, 0.6 + i * (cw + gap), 2.0, cw, 2.0, st[0], st[1], { valueColor: MINT, valueSize: 26 }));
  s.addText("Honest framing: the provable, year-one component of ROI is time-to-insight and action-outcome tracking — both measured directly by the audit ledger and feedback loop already running in this prototype. The larger avoided-risk figure is treated as upside, not the headline.", {
    x: 0.6, y: 4.6, w: 12.1, h: 1.3, fontSize: 14, color: NAVY, fontFace: FONT,
  });
  pageNum(s, 15);
}

// ============ 16. CLOSE ============
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Deterministic core. Generative shell.", {
    x: 0.85, y: 2.5, w: 11.5, h: 1.0, fontSize: 34, bold: true, color: WHITE, fontFace: HEAD,
  });
  s.addText("VANTAGE turns “trust our engine” into “here is the number we measured.”", {
    x: 0.9, y: 3.5, w: 10.8, h: 0.6, fontSize: 18, color: ICE, fontFace: FONT,
  });
  s.addText("Working prototype  ·  Recovery scorecard  ·  Live firewall demo  ·  Business proposal", {
    x: 0.9, y: 4.6, w: 10.8, h: 0.5, fontSize: 14, color: ICE_TXT, fontFace: FONT,
  });
  s.addText("Accenture Innovation Challenge 2026 — Round 2 — Track 3 (BusinessIntelligence.ai)", {
    x: 0.9, y: 6.7, w: 10.8, h: 0.4, fontSize: 12, color: ICE_TXT, fontFace: FONT,
  });
}

pres.writeFile({ fileName: __dirname + "/../VANTAGE_Pitch_Deck.pptx" }).then(() => {
  console.log("Written VANTAGE_Pitch_Deck.pptx");
});
