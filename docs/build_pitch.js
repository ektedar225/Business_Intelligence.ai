const pptxgen = require("pptxgenjs");

// Clean black and white color scheme (ChatGPT-like)
const BLACK = "0d0d0d";
const DARK_GRAY = "1a1a1a";
const MED_GRAY = "404040";
const LIGHT_GRAY = "9b9b9b";
const WHITE = "ffffff";
const ACCENT = "19c37d";  // Clean green accent
const ACCENT_DIM = "e6f7f1";

const FONT = "Inter";
const HEAD = "Inter";

function newDeck() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "VANTAGE Team";
  pres.company = "Accenture Innovation Challenge 2026";
  return pres;
}

function pageNum(slide, n) {
  slide.addText(String(n), {
    x: 12.6, y: 7.05, w: 0.5, h: 0.3, fontSize: 10, color: LIGHT_GRAY, align: "right", fontFace: FONT,
  });
}

const pres = newDeck();

// ============ SLIDE 1: TITLE ============
{
  const s = pres.addSlide();
  s.background = { color: BLACK };
  
  s.addText("ACCENTURE INNOVATION CHALLENGE 2026  ·  ROUND 2  ·  TRACK 3", {
    x: 0.8, y: 1.2, w: 11.7, h: 0.4, fontSize: 11, color: LIGHT_GRAY, charSpacing: 1.2, fontFace: FONT, bold: true,
  });
  
  s.addText("VANTAGE", {
    x: 0.8, y: 2.2, w: 11.7, h: 1.2, fontSize: 64, bold: true, color: WHITE, fontFace: HEAD,
  });
  
  s.addText("KPI Intelligence-to-Action Engine", {
    x: 0.8, y: 3.5, w: 11, h: 0.5, fontSize: 22, color: LIGHT_GRAY, fontFace: FONT,
  });
  
  s.addShape("line", {
    x: 0.8, y: 4.4, w: 2, h: 0, line: { color: ACCENT, width: 3 }
  });
  
  s.addText("The LLM Never Touches a Number", {
    x: 0.8, y: 5.0, w: 10, h: 0.4, fontSize: 18, italics: false, color: ACCENT, fontFace: FONT, bold: true,
  });
  
  s.addText("Every figure is deterministically computed, lineage-traced, and verified before delivery.\nDetects material KPI movements, explains drivers with evidence, and recommends persona-specific actions.", {
    x: 0.8, y: 5.6, w: 11, h: 0.8, fontSize: 13, color: MED_GRAY, fontFace: FONT, lineSpacing: 20,
  });
}

// ============ SLIDE 2: THE PROBLEM ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  pageNum(s, 2);
  
  s.addText("THE PROBLEM", {
    x: 0.8, y: 0.6, w: 11.7, h: 0.4, fontSize: 12, bold: true, color: LIGHT_GRAY, charSpacing: 1.5, fontFace: FONT,
  });
  
  s.addText("Why Current KPI Systems Fall Short", {
    x: 0.8, y: 1.1, w: 11.7, h: 0.7, fontSize: 28, bold: true, color: BLACK, fontFace: HEAD,
  });
  
  const problems = [
    {
      title: "Dashboards Show Symptoms, Not Causes",
      desc: "Most business intelligence tools report that a metric moved, but they cannot explain why it moved or what to do about it."
    },
    {
      title: "Manual Root Cause Analysis Takes Days",
      desc: "Analysts spend days reconciling data from fragmented systems with different refresh cadences and granularities."
    },
    {
      title: "GenAI Wrappers Hallucinate Numbers",
      desc: "Text-to-SQL chatbots are fast at retrieval but fabricate explanations and lack numerical accountability."
    },
    {
      title: "One-Size-Fits-All Insights",
      desc: "Generic explanations ignore role-based decision rights, data entitlements, and actionable levers."
    }
  ];
  
  let yPos = 2.2;
  problems.forEach((p, idx) => {
    s.addShape("roundRect", {
      x: 0.8, y: yPos, w: 11.7, h: 0.95, rectRadius: 0.08,
      fill: { color: idx % 2 === 0 ? "f5f5f5" : "fafafa" },
      line: { type: "none" }
    });
    
    s.addText(`${idx + 1}`, {
      x: 1.0, y: yPos + 0.15, w: 0.5, h: 0.5, fontSize: 20, bold: true, color: ACCENT, fontFace: HEAD, align: "center"
    });
    
    s.addText(p.title, {
      x: 1.7, y: yPos + 0.15, w: 10.5, h: 0.3, fontSize: 14, bold: true, color: BLACK, fontFace: FONT,
    });
    
    s.addText(p.desc, {
      x: 1.7, y: yPos + 0.48, w: 10.5, h: 0.4, fontSize: 11, color: MED_GRAY, fontFace: FONT,
    });
    
    yPos += 1.15;
  });
}

// ============ SLIDE 3: OUR SOLUTION ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  pageNum(s, 3);
  
  s.addText("OUR SOLUTION", {
    x: 0.8, y: 0.6, w: 11.7, h: 0.4, fontSize: 12, bold: true, color: LIGHT_GRAY, charSpacing: 1.5, fontFace: FONT,
  });
  
  s.addText("VANTAGE: Intelligence-to-Action Pipeline", {
    x: 0.8, y: 1.1, w: 11.7, h: 0.7, fontSize: 28, bold: true, color: BLACK, fontFace: HEAD,
  });
  
  s.addText("A hybrid system that separates deterministic computation from narrative generation, ensuring every number is traceable and every insight is actionable.", {
    x: 0.8, y: 1.9, w: 11.7, h: 0.5, fontSize: 13, color: MED_GRAY, fontFace: FONT,
  });
  
  // Architecture flow
  const boxes = [
    { label: "1. DETECT", desc: "Materiality detection\nwith seasonality-aware\nbaselines" },
    { label: "2. RECONCILE", desc: "Multi-source data\nreconciliation across\ndifferent grains" },
    { label: "3. DIAGNOSE", desc: "Attribution ladder:\narithmetic → contribution\n→ event join" },
    { label: "4. COMPOSE", desc: "Evidence bundles\nwith confidence scores\nand lineage" },
    { label: "5. NARRATE", desc: "Persona-specific\nnarratives with\nnumeric firewall" },
    { label: "6. ACT", desc: "Recommended actions\nfiltered by decision\nrights" }
  ];
  
  let xStart = 0.8;
  const boxWidth = 1.85;
  const boxHeight = 1.3;
  const gap = 0.15;
  
  boxes.forEach((box, idx) => {
    const x = xStart + idx * (boxWidth + gap);
    const y = 2.8;
    
    s.addShape("roundRect", {
      x, y, w: boxWidth, h: boxHeight, rectRadius: 0.1,
      fill: { color: "fafafa" },
      line: { color: idx === 4 ? ACCENT : MED_GRAY, width: idx === 4 ? 2 : 1 }
    });
    
    s.addText(box.label, {
      x, y: y + 0.15, w: boxWidth, h: 0.3, fontSize: 11, bold: true, color: BLACK, fontFace: FONT, align: "center"
    });
    
    s.addText(box.desc, {
      x, y: y + 0.5, w: boxWidth, h: 0.7, fontSize: 9, color: MED_GRAY, fontFace: FONT, align: "center", valign: "top"
    });
    
    // Arrow
    if (idx < boxes.length - 1) {
      s.addShape("rightArrow", {
        x: x + boxWidth + 0.02, y: y + 0.55, w: 0.11, h: 0.2,
        fill: { color: MED_GRAY },
        line: { type: "none" }
      });
    }
  });
  
  // Key differentiator
  s.addShape("roundRect", {
    x: 0.8, y: 4.5, w: 11.7, h: 0.85, rectRadius: 0.08,
    fill: { color: ACCENT_DIM },
    line: { color: ACCENT, width: 2 }
  });
  
  s.addText("NUMERIC FIREWALL: Post-narrative validation ensures no orphan numerals or fabricated claims escape to the user.", {
    x: 1.2, y: 4.75, w: 11, h: 0.4, fontSize: 13, bold: true, color: BLACK, fontFace: FONT,
  });
  
  // Bottom stats
  const stats = [
    { value: "100%", label: "Deterministic\nComputation" },
    { value: "0", label: "LLM Calls\nfor Numbers" },
    { value: "<200ms", label: "Analysis\nLatency" },
    { value: "$0.00", label: "Cost per\nInsight" }
  ];
  
  stats.forEach((stat, idx) => {
    const x = 0.8 + idx * 3.0;
    s.addText(stat.value, {
      x, y: 5.7, w: 2.5, h: 0.5, fontSize: 24, bold: true, color: ACCENT, fontFace: HEAD, align: "center"
    });
    s.addText(stat.label, {
      x, y: 6.15, w: 2.5, h: 0.4, fontSize: 10, color: MED_GRAY, fontFace: FONT, align: "center"
    });
  });
}

// ============ SLIDE 4: HOW IT WORKS ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  pageNum(s, 4);
  
  s.addText("ARCHITECTURE", {
    x: 0.8, y: 0.6, w: 11.7, h: 0.4, fontSize: 12, bold: true, color: LIGHT_GRAY, charSpacing: 1.5, fontFace: FONT,
  });
  
  s.addText("Layered Analysis Pipeline", {
    x: 0.8, y: 1.1, w: 11.7, h: 0.7, fontSize: 28, bold: true, color: BLACK, fontFace: HEAD,
  });
  
  const layers = [
    { name: "L1: Reconciliation", desc: "Project heterogeneous sources onto unified calendar with freshness watermarks" },
    { name: "L2: Materiality", desc: "Detect which KPI movements are worth explaining (statistical + business impact)" },
    { name: "L3: Diagnosis Ladder", desc: "Attribution via arithmetic bridge → contribution analysis → event join" },
    { name: "L4: Evidence Bundle", desc: "Immutable, typed, content-hashed object with all facts and lineage" },
    { name: "L5: Confidence & Abstention", desc: "Five-component confidence score + explicit abstention when evidence insufficient" },
    { name: "L6: Narrative + Firewall", desc: "Persona-specific text generation with post-validation of all numerals" },
    { name: "L7: Action Composition", desc: "Filter actions by persona decision rights and recommend levers" },
    { name: "L8: Feedback & Audit", desc: "Beta-Bernoulli weight updates + hash-chained audit ledger" }
  ];
  
  let yPos = 2.2;
  layers.forEach((layer, idx) => {
    s.addShape("roundRect", {
      x: 0.8, y: yPos, w: 11.7, h: 0.6, rectRadius: 0.05,
      fill: { color: idx % 2 === 0 ? "f8f8f8" : WHITE },
      line: { type: "none" }
    });
    
    s.addText(layer.name, {
      x: 1.0, y: yPos + 0.1, w: 3, h: 0.4, fontSize: 12, bold: true, color: BLACK, fontFace: FONT,
    });
    
    s.addText(layer.desc, {
      x: 4.2, y: yPos + 0.1, w: 8, h: 0.4, fontSize: 10, color: MED_GRAY, fontFace: FONT,
    });
    
    yPos += 0.65;
  });
}

// ============ SLIDE 5: PROBLEM STATEMENT ALIGNMENT ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  pageNum(s, 5);
  
  s.addText("COMPLIANCE", {
    x: 0.8, y: 0.6, w: 11.7, h: 0.4, fontSize: 12, bold: true, color: LIGHT_GRAY, charSpacing: 1.5, fontFace: FONT,
  });
  
  s.addText("Problem Statement Requirements: All Met", {
    x: 0.8, y: 1.1, w: 11.7, h: 0.7, fontSize: 28, bold: true, color: BLACK, fontFace: HEAD,
  });
  
  const requirements = [
    { req: "Detect & prioritize material KPI movements", status: "✓ L2 Materiality: seasonal baseline + 2-axis scoring" },
    { req: "Reconcile heterogeneous sources", status: "✓ L1 Reconciliation: multi-grain calendar projection" },
    { req: "Identify & rank explanatory drivers", status: "✓ L3 Diagnosis: 3-method attribution ladder" },
    { req: "Generate persona-specific narratives", status: "✓ L6 Narrative: role-based text with evidence citations" },
    { req: "Communicate uncertainty & abstain", status: "✓ L5 Confidence: 3 abstention modes with resolution paths" },
    { req: "Recommend practical actions", status: "✓ L7 Actions: filtered by decision rights, impact estimates" },
    { req: "Learn from feedback", status: "✓ L8 Feedback: Beta-Bernoulli weight updates persist" },
    { req: "Security, cost, latency constraints", status: "✓ Row/column policies, $0 cost, <200ms latency" }
  ];
  
  let yPos = 2.1;
  requirements.forEach((item, idx) => {
    s.addShape("roundRect", {
      x: 0.8, y: yPos, w: 11.7, h: 0.6, rectRadius: 0.05,
      fill: { color: idx % 2 === 0 ? ACCENT_DIM : WHITE },
      line: { type: "none" }
    });
    
    s.addText(item.req, {
      x: 1.0, y: yPos + 0.1, w: 5, h: 0.4, fontSize: 11, bold: false, color: BLACK, fontFace: FONT,
    });
    
    s.addText(item.status, {
      x: 6.2, y: yPos + 0.1, w: 6, h: 0.4, fontSize: 10, color: MED_GRAY, fontFace: FONT, bold: true,
    });
    
    yPos += 0.67;
  });
}

// ============ SLIDE 6: PROTOTYPE SCENARIOS ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  pageNum(s, 6);
  
  s.addText("DEMONSTRATION", {
    x: 0.8, y: 0.6, w: 11.7, h: 0.4, fontSize: 12, bold: true, color: LIGHT_GRAY, charSpacing: 1.5, fontFace: FONT,
  });
  
  s.addText("Three Working Scenarios", {
    x: 0.8, y: 1.1, w: 11.7, h: 0.7, fontSize: 28, bold: true, color: BLACK, fontFace: HEAD,
  });
  
  const scenarios = [
    {
      num: "1",
      title: "Multi-Factor Movement",
      details: [
        "Net Revenue drop with known injected drivers (price, volume, mix)",
        "Full diagnosis with arithmetic bridge + contribution analysis",
        "Recovery scorecard validates actual driver recall against ground truth",
        "Persona-specific actions (CFO vs Marketing Director)",
        "Demonstrates: heterogeneous sources, confidence scoring, numeric firewall"
      ]
    },
    {
      num: "2",
      title: "Stale Feed Abstention",
      details: [
        "Supply feed is 72 hours stale, blocking reliable diagnosis",
        "Engine explicitly abstains instead of guessing",
        "Explains what's missing, who owns the resolution, and ETA",
        "Demonstrates: data quality flags, abstention modes, uncertainty communication"
      ]
    },
    {
      num: "3",
      title: "Sparse History (New KPI)",
      details: [
        "CAC for a newly launched product family (only 3 weeks of data)",
        "Insufficient history for confident trend detection",
        "Engine states the limitation and what would resolve it",
        "Demonstrates: sparse-history abstention, new product scenario"
      ]
    }
  ];
  
  let yPos = 2.1;
  scenarios.forEach(sc => {
    s.addShape("roundRect", {
      x: 0.8, y: yPos, w: 11.7, h: 1.5, rectRadius: 0.1,
      fill: { color: "fafafa" },
      line: { color: MED_GRAY, width: 1 }
    });
    
    s.addShape("ellipse", {
      x: 1.0, y: yPos + 0.15, w: 0.5, h: 0.5,
      fill: { color: ACCENT },
      line: { type: "none" }
    });
    
    s.addText(sc.num, {
      x: 1.0, y: yPos + 0.15, w: 0.5, h: 0.5,
      fontSize: 18, bold: true, color: WHITE, fontFace: HEAD, align: "center", valign: "middle"
    });
    
    s.addText(sc.title, {
      x: 1.7, y: yPos + 0.2, w: 10.5, h: 0.4, fontSize: 14, bold: true, color: BLACK, fontFace: FONT,
    });
    
    sc.details.forEach((detail, idx) => {
      s.addText(`• ${detail}`, {
        x: 1.7, y: yPos + 0.6 + (idx * 0.18), w: 10.5, h: 0.16, fontSize: 9, color: MED_GRAY, fontFace: FONT,
      });
    });
    
    yPos += 1.65;
  });
}

// ============ SLIDE 7: TECHNOLOGY STACK ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  pageNum(s, 7);
  
  s.addText("IMPLEMENTATION", {
    x: 0.8, y: 0.6, w: 11.7, h: 0.4, fontSize: 12, bold: true, color: LIGHT_GRAY, charSpacing: 1.5, fontFace: FONT,
  });
  
  s.addText("Technology Stack & Deployment", {
    x: 0.8, y: 1.1, w: 11.7, h: 0.7, fontSize: 28, bold: true, color: BLACK, fontFace: HEAD,
  });
  
  const techStack = [
    {
      category: "Core Engine",
      items: "Python 3.10+ | Pandas | NumPy | Pydantic | PyYAML"
    },
    {
      category: "API Layer",
      items: "FastAPI | Uvicorn | CORS middleware"
    },
    {
      category: "Frontend",
      items: "Vanilla JavaScript | HTML5 | CSS3 (no framework dependencies)"
    },
    {
      category: "Testing",
      items: "Pytest suite with ground truth validation"
    },
    {
      category: "Data Sources",
      items: "CSV/JSONL (demo) | Extensible to SQL, Snowflake, Databricks, Fabric"
    },
    {
      category: "Deployment",
      items: "Containerized (Docker) | Cloud-ready (AWS/Azure/GCP)"
    }
  ];
  
  let yPos = 2.2;
  techStack.forEach((tech, idx) => {
    s.addShape("roundRect", {
      x: 0.8, y: yPos, w: 11.7, h: 0.7, rectRadius: 0.05,
      fill: { color: idx % 2 === 0 ? "f8f8f8" : WHITE },
      line: { type: "none" }
    });
    
    s.addText(tech.category, {
      x: 1.0, y: yPos + 0.15, w: 2.5, h: 0.4, fontSize: 12, bold: true, color: BLACK, fontFace: FONT,
    });
    
    s.addText(tech.items, {
      x: 3.8, y: yPos + 0.15, w: 8.5, h: 0.4, fontSize: 10, color: MED_GRAY, fontFace: FONT,
    });
    
    yPos += 0.75;
  });
  
  // Separator
  s.addShape("line", {
    x: 0.8, y: yPos + 0.2, w: 11.7, h: 0, line: { color: MED_GRAY, width: 1, dashType: "dash" }
  });
  
  s.addText("LLM vs Non-LLM Breakdown", {
    x: 0.8, y: yPos + 0.5, w: 11.7, h: 0.4, fontSize: 14, bold: true, color: BLACK, fontFace: FONT,
  });
  
  s.addText("Deterministic (Python): Detection, reconciliation, attribution, confidence, action composition, firewall validation, audit logging", {
    x: 0.8, y: yPos + 0.95, w: 5.5, h: 0.6, fontSize: 10, color: MED_GRAY, fontFace: FONT,
  });
  
  s.addText("Optional LLM: Narrative phrasing only (T0 template used in prototype = 0 model calls, $0 cost)", {
    x: 6.5, y: yPos + 0.95, w: 5.8, h: 0.6, fontSize: 10, color: MED_GRAY, fontFace: FONT,
  });
}

// ============ SLIDE 8: BUSINESS VALUE ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  pageNum(s, 8);
  
  s.addText("IMPACT", {
    x: 0.8, y: 0.6, w: 11.7, h: 0.4, fontSize: 12, bold: true, color: LIGHT_GRAY, charSpacing: 1.5, fontFace: FONT,
  });
  
  s.addText("Business Value & Scalability", {
    x: 0.8, y: 1.1, w: 11.7, h: 0.7, fontSize: 28, bold: true, color: BLACK, fontFace: HEAD,
  });
  
  const valueProps = [
    {
      title: "Speed to Action",
      metric: "Days → Minutes",
      desc: "Reduces root cause analysis from manual analyst days to sub-second automated diagnosis, enabling real-time decision-making."
    },
    {
      title: "Democratized Intelligence",
      metric: "Zero SQL Required",
      desc: "Empowers non-technical executives to understand KPI movements without waiting for the analytics team."
    },
    {
      title: "Trust & Auditability",
      metric: "100% Traceable",
      desc: "Every number cites its source tables, method, and lineage. Hash-chained audit log for compliance."
    },
    {
      title: "Cost Efficiency",
      metric: "$0 per Insight",
      desc: "Template-tier narrative generation eliminates LLM API costs while maintaining quality and accountability."
    }
  ];
  
  valueProps.forEach((vp, idx) => {
    const x = 0.8 + (idx % 2) * 6.0;
    const y = 2.2 + Math.floor(idx / 2) * 1.8;
    
    s.addShape("roundRect", {
      x, y, w: 5.7, h: 1.5, rectRadius: 0.1,
      fill: { color: "fafafa" },
      line: { color: MED_GRAY, width: 1 }
    });
    
    s.addText(vp.title, {
      x: x + 0.2, y: y + 0.15, w: 5.3, h: 0.3, fontSize: 13, bold: true, color: BLACK, fontFace: FONT,
    });
    
    s.addText(vp.metric, {
      x: x + 0.2, y: y + 0.5, w: 5.3, h: 0.35, fontSize: 18, bold: true, color: ACCENT, fontFace: HEAD,
    });
    
    s.addText(vp.desc, {
      x: x + 0.2, y: y + 0.9, w: 5.3, h: 0.5, fontSize: 10, color: MED_GRAY, fontFace: FONT,
    });
  });
  
  // Enterprise scalability
  s.addShape("roundRect", {
    x: 0.8, y: 5.8, w: 11.7, h: 0.9, rectRadius: 0.08,
    fill: { color: ACCENT_DIM },
    line: { color: ACCENT, width: 2 }
  });
  
  s.addText("ENTERPRISE SCALABILITY", {
    x: 1.0, y: 5.95, w: 11.3, h: 0.25, fontSize: 11, bold: true, color: BLACK, fontFace: FONT,
  });
  
  s.addText("Department-agnostic design: Adding new KPIs (Sales → Supply Chain → HR) requires only YAML config changes, not code rewrites. Horizontal scaling via containerization. Integration-ready with Snowflake, Databricks, Microsoft Fabric, Tableau, and Looker.", {
    x: 1.0, y: 6.25, w: 11.3, h: 0.4, fontSize: 10, color: MED_GRAY, fontFace: FONT,
  });
}

// ============ SLIDE 9: NEXT STEPS ============
{
  const s = pres.addSlide();
  s.background = { color: BLACK };
  pageNum(s, 9);
  
  s.addText("NEXT STEPS", {
    x: 0.8, y: 1.5, w: 11.7, h: 0.4, fontSize: 12, bold: true, color: LIGHT_GRAY, charSpacing: 1.5, fontFace: FONT,
  });
  
  s.addText("From Prototype to Production", {
    x: 0.8, y: 2.0, w: 11.7, h: 0.8, fontSize: 28, bold: true, color: WHITE, fontFace: HEAD,
  });
  
  const steps = [
    "Connect to real enterprise data sources (Snowflake, Databricks, SQL warehouses)",
    "Expand KPI registry to cover cross-functional metrics (Finance, Marketing, Supply Chain, HR)",
    "Integrate causal inference methods for stronger counterfactual reasoning",
    "Build proactive alert system for real-time monitoring and Slack/Teams delivery",
    "Deploy tier-2 LLM narrative generation for complex, multi-driver scenarios",
    "Establish continuous learning loop with expert validation and A/B testing"
  ];
  
  let yPos = 3.2;
  steps.forEach((step, idx) => {
    s.addText(`${idx + 1}`, {
      x: 0.8, y: yPos, w: 0.4, h: 0.4, fontSize: 16, bold: true, color: ACCENT, fontFace: HEAD, align: "center"
    });
    
    s.addText(step, {
      x: 1.4, y: yPos + 0.05, w: 11, h: 0.3, fontSize: 12, color: LIGHT_GRAY, fontFace: FONT,
    });
    
    yPos += 0.55;
  });
  
  s.addShape("line", {
    x: 0.8, y: 6.3, w: 2, h: 0, line: { color: ACCENT, width: 3 }
  });
  
  s.addText("Don't Just Look at Your Data. Understand It.", {
    x: 0.8, y: 6.6, w: 11.7, h: 0.5, fontSize: 20, italics: false, color: WHITE, fontFace: HEAD, bold: true,
  });
}

pres.writeFile({ fileName: "VANTAGE_Pitch_Deck.pptx" });
console.log("✓ VANTAGE_Pitch_Deck.pptx generated successfully");
