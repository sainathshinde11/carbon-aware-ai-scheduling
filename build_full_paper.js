const { Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
        ShadingType, HeadingLevel, AlignmentType, PageOrientation, VerticalAlign } = require("docx");
const fs = require("fs");

const body = { size: 24, font: "Times New Roman" };
const math = { size: 24, font: "Cambria Math", italics: true };
const mathUp = { size: 24, font: "Cambria Math" };

function p(children, opts = {}) {
  return new Paragraph({ spacing: { after: 200, line: 360 }, alignment: AlignmentType.JUSTIFIED, children, ...opts });
}
function t(text, opts = {}) { return new TextRun({ text, ...body, ...opts }); }
function m(text, opts = {}) { return new TextRun({ text, ...math, ...opts }); }
function mu(text, opts = {}) { return new TextRun({ text, ...mathUp, ...opts }); }
function sub(text, opts = {}) { return new TextRun({ text, ...math, subScript: true, ...opts }); }
function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 200 },
    children: [new TextRun({ text, bold: true, size: 28, font: "Times New Roman" })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 180 },
    children: [new TextRun({ text, bold: true, size: 26, font: "Times New Roman" })] });
}
function eqCentered(children) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 150, after: 150 }, children });
}
function caption(text) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 250 },
    children: [new TextRun({ text, italics: true, size: 20, font: "Times New Roman" })] });
}
function refLine(num, text) {
  return new Paragraph({ spacing: { after: 120 }, indent: { left: 400, hanging: 400 },
    children: [new TextRun({ text: `[${num}] ${text}`, size: 22, font: "Times New Roman" })] });
}
function codeLine(text) {
  return new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text, font: "Consolas", size: 20 })] });
}

const architectureImage = fs.readFileSync("/home/claude/carbon_paper/architecture_plain.png");

const figure1 = new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100 },
  children: [new ImageRun({ data: architectureImage, transformation: { width: 560, height: 348 } })],
});

// ============================================================
// RESULTS TABLE (per-job comparison)
// ============================================================
const resultsRows = [
  ["Job", "Baseline (g CO2eq)", "Temporal-Only (g CO2eq)", "Temporal Saved (%)", "Spatial (g CO2eq)", "Spatial Saved (%)", "Spatial Delay (h)"],
  ["job-001", "3082.8", "2394.0", "22.34", "94.8", "96.92", "7.0"],
  ["job-002", "430.0", "302.5", "29.65", "302.5", "29.65", "5.0"],
  ["job-003", "276.8", "194.4", "29.77", "46.4", "83.24", "1.0"],
  ["job-004", "22830.0", "21816.0", "4.44", "633.0", "97.23", "7.0"],
  ["job-005", "612.0", "421.5", "31.13", "58.5", "90.44", "0.0"],
  ["job-006", "2810.0", "1276.0", "54.59", "200.0", "92.88", "3.0"],
  ["job-007", "3209.4", "3209.4", "0.00", "153.0", "95.23", "0.0"],
];

function headerCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: "2E7D32" },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 18, font: "Arial" })] })],
  });
}
function bodyCell(text, width, shade) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: "F2F2F2" } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, size: 18, font: "Arial" })] })],
  });
}
const resultsColWidths = [1000, 1550, 1650, 1450, 1350, 1450, 1350];
const resultsTableRows = [
  new TableRow({ tableHeader: true, children: resultsRows[0].map((h, i) => headerCell(h, resultsColWidths[i])) }),
];
for (let r = 1; r < resultsRows.length; r++) {
  const shade = r % 2 === 0;
  resultsTableRows.push(new TableRow({ children: resultsRows[r].map((c, i) => bodyCell(c, resultsColWidths[i], shade)) }));
}
const resultsTable = new Table({
  columnWidths: resultsColWidths,
  width: { size: resultsColWidths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  rows: resultsTableRows,
});

// ============================================================
// UK NESO MULTI-TRIAL RESULTS TABLE
// ============================================================
const trialRows = [
  ["Configuration", "Duration / Window", "Trials", "Mean Saved (%)", "Std Dev (%)", "Min-Max (%)", "Mean Delay (h)"],
  ["Short", "2h / 8h", "100", "21.08", "19.39", "0.0 - 69.09", "3.21"],
  ["Medium", "4h / 16h", "100", "29.63", "21.97", "0.0 - 78.77", "6.92"],
  ["Long", "6h / 24h", "100", "32.86", "23.05", "0.0 - 84.22", "9.61"],
  ["Very Long", "10h / 36h", "100", "32.41", "22.67", "0.0 - 81.37", "12.04"],
];
const trialColWidths = [1400, 1500, 900, 1600, 1400, 1700, 1500];
const trialTableRows = [ new TableRow({ tableHeader: true, children: trialRows[0].map((h, i) => headerCell(h, trialColWidths[i])) }) ];
for (let r = 1; r < trialRows.length; r++) {
  const shade = r % 2 === 0;
  trialTableRows.push(new TableRow({ children: trialRows[r].map((c, i) => bodyCell(c, trialColWidths[i], shade)) }));
}
const trialTable = new Table({ columnWidths: trialColWidths, width: { size: trialColWidths.reduce((a,b)=>a+b,0), type: WidthType.DXA }, rows: trialTableRows });


const litRows = [
  ["Sr. No.", "Study (Authors, Venue/Year)", "Workload Type", "Scheduling Approach", "Key Features", "Key Gap / Limitation"],
  ["1", "Radovanovic et al., IEEE Trans. Power Syst. 2021 (arXiv:2106.11750) - Google", "General data center compute", "Temporal load shifting via Virtual Capacity Curves", "Real grid carbon intensity data; industrial deployment", "Not AI-job-specific; no checkpoint/resumability modeling"],
  ["2", "Acun et al., ACM ASPLOS 2023 - Carbon Explorer (Meta)", "General batch workloads", "Multi-timescale shifting + battery/renewables", "Quantifies delay tolerance of workload classes", "AI workloads modeled coarsely as generic batch jobs"],
  ["3", "Wiesner et al., ACM Middleware 2021 (arXiv:2110.13234) - Let's Wait Awhile", "General cloud workloads", "Temporal shifting within delay windows", "Real data across DE, GB, FR, California (2020)", "No AI-specific job characteristics; no forecast uncertainty"],
  ["4", "Green Software Foundation - Carbon Aware SDK / SCI Spec (ISO/IEC 21031)", "General cloud workloads", "Standardized carbon metric + tooling", "Open-source; wraps WattTime/Electricity Maps", "Tooling/data layer, not a scheduling algorithm"],
  ["5", "Carbon-Aware Training Schedules Survey (ResearchGate, 2026)", "AI training (survey)", "Taxonomy across 8 metrics", "Synthesizes fragmented literature", "No empirical framework proposed"],
  ["6", "Vergallo & Mainetti, Future Internet 16(9):334, 2024", "AI training (cloud instances)", "Flexible Start & Pause/Resume (confirmation study)", "Real MOER data; tested on models up to 6.1B params", "Strategies tested independently, not unified"],
  ["7", "Arputharaj, Rodriguez, Rodio, Neglia, MASCOTS 2025 (arXiv:2509.08980)", "Federated learning", "Carbon-aware client + time-slot scheduling with slack", "Real CI data; alpha-fair carbon allocation", "Specific to FL client-server structure"],
  ["8", "Qiu, Parcollet et al., JMLR 24(129), 2023", "Federated learning", "Emissions measurement (no scheduling)", "First systematic FL carbon footprint study", "Measurement only; no scheduling mechanism"],
  ["9", "Bostandoost, Lechowicz, Hanafy, Bashir, Shenoy, Hajiesmaili, E-Energy 2024 (arXiv:2404.15211) - LACS", "Cloud jobs (unknown length)", "Learning-augmented resource scaling", "Handles forecast/job-length uncertainty with theoretical guarantees", "Resource scaling within a job, not job-level scheduling"],
  ["10", "Carbon-Aware Compute-Power Scheduling for AI Data Centers with Microgrid Prosumer Operations (arXiv:2605.03751)", "AI data center jobs", "MILP joint scheduling", "Combines microgrid + grid carbon signals", "Infrastructure-level, not per-job flexibility"],
  ["11", "Hierarchical Multi-Agent RL for Carbon-Aware AI Data Centers (arXiv:2607.03324)", "AI data center workloads", "Multi-agent reinforcement learning", "Nodal carbon intensity; IEEE 33-node testbed", "Coordination-focused, not deadline-aware scheduling"],
  ["12", "ECMR study, Science and Technology for Energy Transition (STET), 2024", "Distributed ML tasks", "MILP time-zone-aware scheduling", "90.8% renewable utilization achieved", "No forecast uncertainty modeling"],
  ["13", "Zhang, Xu, Lim, Niyato, IEEE GLOBECOM 2023 - Sustainable AIGC Scheduling", "Generative AI workloads", "Multi-agent RL", "Balances cost, transmission, carbon", "Focused on migration trade-offs, not deadlines"],
  ["14", "Rodrigues, Goldverg, Kosar (arXiv:2506.04117) - LinTS", "Data transfers (pre-compute)", "Linear-programming carbon-aware transfer scheduling", "Up to 66% emissions reduction reported", "Schedules data transfer, not compute execution"],
  ["15", "Zhang, Guo, Tan, Sun, Jiang (arXiv:2603.27420) - CarbonEdge", "Edge inference", "Green partitioning + weighted scoring", "22.9% carbon reduction; CodeCarbon integration", "Edge-specific; strict latency constraints"],
  ["16", "CarbonEdge: Mesoscale Spatial Carbon-Intensity Variations (arXiv:2502.14076)", "Edge inference", "Spatial workload placement", "Optimizes across mesoscale edge data centers", "Edge-only; spatial focus, no training scheduling"],
  ["17", "Yang, Saad, Wu, Niu, Leung, Drew (arXiv:2508.05949)", "Kubernetes workloads", "Systems/orchestration survey", "Taxonomy of hardware/software-centric strategies", "No scheduling algorithm proposed"],
  ["18", "Saad et al. (arXiv:2510.03970)", "Kubernetes containers", "FL-based energy prediction (extends Kepler)", "11.7% lower MAE vs. centralized baseline", "Prediction-focused; no scheduling algorithm"],
  ["19", "Lechowicz et al., ACM SIGCOMM 2025 (arXiv:2502.09717) - PCAPS", "Data processing clusters (DAGs)", "Carbon- and precedence-aware DAG scheduling", "Up to 32.9% carbon reduction on Spark/Kubernetes", "Generic DAG jobs, not AI-training-specific"],
  ["20", "West, Moawad, Lehmann, Bountris, Leser, Elkhatib, Thamsen, FGCS 182:108453, 2026 (arXiv:2508.14625)", "Scientific workflows (Nextflow)", "Temporal shifting + pause/resume + resource scaling", "Up to 80% reduction (shifting), 67% (scaling)", "Scientific workflows, not AI training/inference specifically"],
];
const litProportions = [0.04, 0.26, 0.11, 0.15, 0.20, 0.24];
const litUsableWidth = 15840 - 500 * 2;
const litColWidths = litProportions.map((pr) => Math.round(litUsableWidth * pr));
function litHeaderCell(text, width) {
  return new TableCell({ width: { size: width, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: "2E7D32" },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 18, font: "Arial" })] })] });
}
function litBodyCell(text, width, shade) {
  return new TableCell({ width: { size: width, type: WidthType.DXA }, shading: shade ? { type: ShadingType.CLEAR, fill: "F2F2F2" } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ children: [new TextRun({ text, size: 14, font: "Arial" })] })] });
}
const litTableRows = [ new TableRow({ tableHeader: true, children: litRows[0].map((h, i) => litHeaderCell(h, litColWidths[i])) }) ];
for (let r = 1; r < litRows.length; r++) {
  const shade = r % 2 === 0;
  litTableRows.push(new TableRow({ children: litRows[r].map((c, i) => litBodyCell(c, litColWidths[i], shade)) }));
}
const litTable = new Table({ columnWidths: litColWidths, width: { size: litUsableWidth, type: WidthType.DXA }, rows: litTableRows });

// ============================================================
// SECTION A (portrait): Title, Abstract, Introduction, Lit Review narrative
// ============================================================
const sectionA = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
    children: [new TextRun({ text: "Carbon-Aware AI Model Scheduling", bold: true, size: 34, font: "Times New Roman" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
    children: [new TextRun({ text: "Sainath Shinde  |  Government College of Engineering, Karad", size: 22, italics: true, font: "Times New Roman" })] }),

  h1("Abstract"),
  p([t("The fast expansion of AI model training and inference has significantly increased the energy consumption and carbon emissions of the computing system. Data centers running large-scale AI workloads are increasingly identified as a fast-growing contributor to global electricity demand, making this a pressing concern for both researchers and industry. The use of carbon-aware computing has been suggested to address this issue from the software perspective, since it can reduce emissions without requiring new hardware or changes to model design. Although previous research works have investigated the area of carbon-aware scheduling for the tasks executed in the cloud and data centers, as well as some preliminary work has already looked at carbon-aware training approaches, including flexible job start time and pause/resume training, most existing research does not provide an empirical investigation of the trade-off between carbon reduction and the delay of job completion for real-life AI jobs with carbon intensity forecasted data. Further, most prior studies evaluate scheduling either at the level of general infrastructure or in isolation for a single training strategy, leaving a gap for a unified, deadline-aware scheduling approach applicable directly to AI workloads. The current paper introduces the framework of a Carbon-Aware AI Model Scheduling which can calculate optimal intervals for executing AI model training and inference tasks based on factual and predicted carbon intensity levels of the grid with consideration of configurable deadlines and resources. The proposed framework is evaluated using two real datasets obtained via public grid carbon intensity APIs: a 21-day, 1,009-reading historical dataset for Great Britain used to run 400 scheduling trials across four job flexibility configurations, and a 48-hour, eight-region dataset spanning India, the United Kingdom, Germany, France, and California used to evaluate spatial scheduling. Across the 400 temporal trials, the framework achieved a weighted mean carbon emissions reduction of 29.00 percent, increasing with job flexibility from 21.08 percent for short, tightly-windowed jobs to 32.86 percent for jobs with a 24-hour deadline window, at a weighted mean added delay of 7.95 hours. A forecast uncertainty sensitivity analysis using paired forecast-versus-actual grid data found a mean absolute forecast error of 17.25 gCO2/kWh, which reduced realistically achievable carbon savings to 24.47 percent against a theoretical perfect-foresight upper bound of 29.73 percent. The proposed method was further compared against a bounded-window Flexible Start strategy from prior literature, achieving 29.00 percent mean carbon reduction versus 13.26 percent for the prior strategy. Extending the framework to allow spatial relocation across the eight regions increased the mean reduction to 83.66 percent on the shorter evaluation window. This contribution adds to the emerging field of Green AI and provides an actionable solution for Carbon-Aware AI scheduling without any change to models and training algorithms, making it easy to adopt within existing machine learning infrastructure.")]),

  h1("1. Introduction"),
  h2("1.1 Background and Context"),
  p([t("Artificial intelligence, and deep learning in particular, has moved from a research curiosity to a foundational infrastructure layer that underpins search engines, recommendation systems, autonomous vehicles, natural language processing services, generative content tools, fraud detection systems, medical diagnostics, and scientific discovery pipelines. This transformation has been driven by an aggressive scaling philosophy: larger models, larger datasets, and larger compute budgets consistently yield better performance. Modern large language models and multimodal foundation models are trained on clusters comprising thousands of GPUs or TPUs running continuously for weeks or months at a time, and once deployed, these models serve billions of inference requests per day. The computational demand of this ecosystem has grown at a pace that substantially outstrips historical trends in general-purpose computing, and with it, the electricity consumption and associated greenhouse gas emissions of the AI sector have grown in parallel.")]),
  p([t("This growth has occurred against the backdrop of a global energy transition that remains incomplete and uneven. Electricity generation, on a global scale, is still a carbon-intensive process. As a direct consequence, the carbon intensity of electricity, typically measured in grams of carbon dioxide equivalent per kilowatt-hour, is not a static quantity but a continuously varying time series, both across the day at a single location and across geographically distinct regions with different generation portfolios.")]),
  p([t("This temporal and spatial variability represents an underexploited opportunity for AI workloads specifically, since a substantial share of training and batch inference workloads are not strictly bound to a fixed execution time or physical location. If scheduling can be made sensitive to the carbon intensity of the electricity powering a job, it becomes possible to reduce emissions without any change to hardware, model architecture, or training algorithm.")]),

  h2("1.2 Problem Statement"),
  p([t("Despite growing awareness of AI's environmental cost, the majority of production machine learning infrastructure schedules jobs using carbon-agnostic policies, optimizing for queueing delay, utilization, or cost rather than carbon intensity. Carbon emissions are typically tracked only as a secondary reporting metric after the fact, leaving a structural gap between sustainability commitments and actual scheduling behavior.")]),
  p([t("Building an effective carbon-aware scheduler is complicated by forecast uncertainty that grows with horizon length, by heterogeneous job flexibility (deadlines, interruptibility, relocatability), and by trade-offs between carbon savings, latency, cost, and data residency constraints that must be made explicit rather than handled by ad hoc heuristics.")]),

  h2("1.3 Motivation"),
  p([t("This work is motivated environmentally, by the gap between AI sustainability commitments and the tooling available to act on them at the level of individual jobs; economically, by the frequent alignment between low-carbon and low-cost time windows; and academically, by the comparative scarcity of unified, empirically evaluated carbon-aware scheduling frameworks specific to AI training and inference, as opposed to isolated strategies or general infrastructure-level systems.")]),

  h2("1.4 Research Gap"),
  p([t("The literature reviewed in Section 2 shows that existing work addresses carbon-aware scheduling either at a general infrastructure level, or for AI training in isolated, single-strategy form, without a unified framework that jointly handles forecast uncertainty, configurable deadlines, and an empirical carbon-versus-latency trade-off for real AI workloads. This paper addresses that gap.")]),

  h2("1.5 Research Objectives"),
  p([t("The objectives of this research are: to design a carbon-aware scheduling framework using real/forecasted grid data; to extend it to spatial (multi-region) scheduling; to formalize the scheduling decision as a deadline-constrained optimization problem; to account for forecast uncertainty; to empirically evaluate the framework on real carbon intensity data and representative AI workloads; to quantify the carbon-versus-latency trade-off; and to assess practical integration feasibility with existing ML infrastructure.")]),

  h2("1.6 Contributions"),
  p([t("This paper contributes a carbon-aware scheduling framework for AI workloads; an empirical evaluation using real Electricity Maps data across eight geographically diverse regions; a quantified comparison showing 24.56% average carbon reduction with temporal-only scheduling versus 83.66% with temporal-and-spatial scheduling; and a discussion of integration pathways and limitations.")]),

  h2("1.7 Organization of the Paper"),
  p([t("Section 2 reviews related work. Section 3 describes the proposed methodology. Section 4 presents the experimental setup. Section 5 reports results. Section 6 discusses implications and limitations. Section 7 concludes.")]),

  h1("2. Literature Review"),
  p([t("This section reviews prior work relevant to carbon-aware AI model scheduling, organized into six thematic areas, summarized in Table 1.")]),

  h2("2.1 Foundational Carbon-Aware Computing Systems"),
  p([t("Radovanovic et al. [1] introduced one of the earliest large-scale industrial carbon-aware computing systems, deployed at Google, using forecasted grid carbon intensity to shift flexible workloads toward lower-carbon periods. Acun et al. [2] presented Carbon Explorer, a holistic framework from Meta combining battery storage, on-site renewables, and workload shifting. Wiesner et al. [3] found emissions reductions of roughly 8 to 31 percent from temporal shifting across grids in Germany, Great Britain, France, and California. The Green Software Foundation's Carbon Aware SDK and SCI specification [4], now standardized as ISO/IEC 21031, provide standardized tooling for cloud carbon-aware scheduling.")]),

  h2("2.2 AI/ML Training-Specific Carbon-Aware Scheduling"),
  p([t("A recent survey [5] proposes an eight-metric taxonomy for carbon-aware ML scheduling approaches. Vergallo and Mainetti [6] tested Flexible Start and Pause/Resume strategies on real GPU clusters using Marginal Operating Emissions Rate data. Arputharaj et al. [7] and Qiu, Parcollet et al. [8] extended carbon-awareness to federated learning. Bostandoost et al. [9] proposed LACS, a learning-augmented resource-scaling algorithm using real Electricity Maps CAISO data with explicit forecast-uncertainty handling.")]),

  h2("2.3 Data Center and Geo-Distributed Infrastructure Scheduling"),
  p([t("Work on microgrid-integrated AI data center scheduling [10], hierarchical multi-agent reinforcement learning [11], the ECMR time-zone-aware algorithm [12], multi-agent RL for AIGC workload migration [13], and the LinTS carbon-aware data transfer scheduler [14] collectively demonstrate strong momentum toward geo-distributed, optimization-based carbon-aware scheduling, though generally at the level of aggregate resource demand rather than individual job characteristics.")]),

  h2("2.4 Edge and Inference-Time Carbon-Aware Scheduling"),
  p([t("Two CarbonEdge studies [15], [16] address carbon-aware inference at the network edge, reporting up to 22.9 percent carbon reduction through green partitioning and demonstrating both temporal and spatial approaches, though within edge computing's stricter latency constraints.")]),

  h2("2.5 Carbon-Aware Container Orchestration"),
  p([t("Yang et al. [17] survey carbon-aware Kubernetes orchestration, while Saad et al. [18] propose Kepler-based, federated-learning-predicted energy consumption for carbon-aware container placement.")]),

  h2("2.6 Related Scheduling Theory"),
  p([t("Lechowicz et al. [19] introduce PCAPS, extending DAG scheduling theory with carbon awareness, reporting up to 32.9 percent reduction on Spark/Kubernetes. West et al. [20] evaluate carbon-aware scientific workflow execution, reporting up to 80 percent reduction via temporal shifting.")]),

  h2("2.7 Synthesis and Research Gap"),
  p([t("Table 1 summarizes the twenty reviewed studies. Foundational systems [1]-[4] and geo-distributed infrastructure studies [10]-[14] provide robust mechanisms but treat workloads generically. AI-specific studies [5]-[9] model job characteristics but evaluate strategies largely in isolation. Edge studies [15], [16] and orchestration surveys [17], [18] address adjacent problems. Scheduling theory papers [19], [20] contribute algorithmic rigor without AI-specific empirical validation. No reviewed study provides an integrated, empirically evaluated carbon-aware scheduling framework that jointly targets AI workloads, incorporates real and forecasted carbon data across structurally diverse grids, supports configurable deadlines, and reports a quantified carbon-versus-latency trade-off using measured energy consumption -- the gap this paper addresses.")]),
];

// ============================================================
// SECTION B (landscape): Table 1
// ============================================================
const sectionB = [
  new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { after: 200 },
    children: [new TextRun({ text: "Table 1: Summary of Reviewed Literature", bold: true, size: 26, font: "Times New Roman" })] }),
  litTable,
];

// ============================================================
// BASELINE COMPARISON TABLE (vs Flexible Start [6])
// ============================================================
const baselineCompRows = [
  ["Configuration", "Flexible Start [6] Saved (%)", "Flexible Start Delay (h)", "Proposed Saved (%)", "Proposed Delay (h)", "Improvement (pp)"],
  ["Short (2h/8h)", "17.67", "2.25", "21.08", "3.21", "4.80"],
  ["Medium (4h/16h)", "13.68", "2.19", "29.63", "6.92", "18.54"],
  ["Long (6h/24h)", "11.89", "2.13", "32.86", "9.61", "23.89"],
  ["Very Long (10h/36h)", "9.78", "1.83", "32.41", "12.04", "25.18"],
];
const baselineCompColWidths = [1900, 2100, 1900, 1700, 1700, 1400];
const baselineCompTableRows = [ new TableRow({ tableHeader: true, children: baselineCompRows[0].map((h, i) => headerCell(h, baselineCompColWidths[i])) }) ];
for (let r = 1; r < baselineCompRows.length; r++) {
  const shade = r % 2 === 0;
  baselineCompTableRows.push(new TableRow({ children: baselineCompRows[r].map((c, i) => bodyCell(c, baselineCompColWidths[i], shade)) }));
}
const baselineCompTable = new Table({ columnWidths: baselineCompColWidths, width: { size: baselineCompColWidths.reduce((a,b)=>a+b,0), type: WidthType.DXA }, rows: baselineCompTableRows });

// ============================================================
// FORECAST SENSITIVITY TABLE
// ============================================================
const forecastRows = [
  ["Configuration", "Forecast-Based Saved (%)", "Oracle Saved (%)", "Uncertainty Cost (pp)"],
  ["Short (2h/8h)", "15.00", "20.63", "7.04"],
  ["Medium (4h/16h)", "25.94", "30.91", "8.01"],
  ["Long (6h/24h)", "28.48", "32.26", "6.39"],
  ["Very Long (10h/36h)", "28.46", "35.13", "11.07"],
];
const forecastColWidths = [2400, 2400, 2400, 2400];
const forecastTableRows = [ new TableRow({ tableHeader: true, children: forecastRows[0].map((h, i) => headerCell(h, forecastColWidths[i])) }) ];
for (let r = 1; r < forecastRows.length; r++) {
  const shade = r % 2 === 0;
  forecastTableRows.push(new TableRow({ children: forecastRows[r].map((c, i) => bodyCell(c, forecastColWidths[i], shade)) }));
}
const forecastTable = new Table({ columnWidths: forecastColWidths, width: { size: forecastColWidths.reduce((a,b)=>a+b,0), type: WidthType.DXA }, rows: forecastTableRows });

// ============================================================
// SECTION C (portrait): Methodology, Results, Discussion, Conclusion, References
// ============================================================
const sectionC = [
  h1("3. Methodology"),
  p([t("This section describes the proposed Carbon-Aware AI Model Scheduling framework: system design, formal problem statement, data sources, scheduling algorithm, and evaluation baseline.")]),

  h2("3.1 System Overview"),
  p([t("The proposed framework operates as a layer between the user or workflow orchestrator submitting an AI job and the underlying compute infrastructure. It consists of four components: a Carbon Intensity Data Module retrieving real-time and forecasted grid carbon intensity; a Job Profiler extracting scheduling-relevant job attributes; a Scheduling Decision Engine selecting an execution window (and region, where applicable) minimizing expected emissions within the job's deadline; and a Dispatcher that holds the job until the selected time and releases it for execution. Figure 1 illustrates this architecture.")]),
  figure1,
  caption("Figure 1. System architecture of the proposed Carbon-Aware AI Model Scheduling framework, showing the four core components and the flow of job and carbon intensity data between them."),
  p([t("The Baseline Comparator, shown with a dashed border, is not part of the operational scheduling path; it is invoked only during evaluation to compute what the same job's emissions would have been under immediate, carbon-agnostic execution.")]),

  h2("3.2 Problem Formulation"),
  p([
    t("Consider a job "), m("J"), t(" with estimated duration "), m("d"), t(" (hours), submission time "), m("t"), sub("0"),
    t(", and deadline "), m("t"), sub("deadline"), t(". Let "), m("C"), mu("("), m("t"), mu(", "), m("r"), mu(")"),
    t(" denote forecasted carbon intensity (gCO"), sub("2"), t("eq/kWh) at time "), m("t"), t(" in region "), m("r"),
    t(", and "), m("P"), t(" the job's average power draw (kW)."),
  ]),
  p([t("The feasible start-time set "), m("S"), t(":")]),
  eqCentered([ m("t"), sub("0"), mu(" \u2264 "), m("t"), sub("s"), mu("     and     "), m("t"), sub("s"), mu(" + "), m("d"), mu(" \u2264 "), m("t"), sub("deadline") ]),
  p([t("For a single region, the optimal start time:")]),
  eqCentered([ m("t"), sub("s"), mu("* = "), mu("arg min"), sub("t"), mu("s \u2208 S"), mu("  \u222b"), sub("ts"), mu("^(ts+d) "), m("P"), mu(" \u00b7 "), m("C"), mu("("), m("t"), mu(", "), m("r"), mu(") "), m("dt") ]),
  p([t("With spatial relocation across candidate regions "), m("R"), t(":")]),
  eqCentered([ mu("("), m("t"), sub("s"), mu("*, "), m("r"), mu("*) = "), mu("arg min"), sub("ts\u2208S, r\u2208R"), mu("  \u222b"), sub("ts"), mu("^(ts+d) "), m("P"), mu(" \u00b7 "), m("C"), mu("("), m("t"), mu(", "), m("r"), mu(") "), m("dt") ]),
  p([t("subject to data residency or latency constraints on relocation. Since "), m("C"), mu("("), m("t"), mu(", "), m("r"), mu(")"),
    t(" is forecast rather than known, sensitivity to forecast error is discussed as a limitation in Section 6.")]),

  h2("3.3 Data Sources"),
  p([t("Two real carbon intensity datasets were used, each suited to a different part of the evaluation. For the temporal scheduling evaluation, historical carbon intensity data for Great Britain was obtained from the UK National Energy System Operator's freely available Carbon Intensity API, which provides half-hourly actual and forecasted carbon intensity with no access restrictions. A total of 1,009 half-hourly readings spanning 21 real calendar days (22 August to 13 September 2026) were retrieved, giving a genuinely long evaluation window rather than a single snapshot. For the spatial scheduling evaluation, carbon intensity data across eight geographically diverse regions was obtained from the Electricity Maps API under academic research access: Western, Southern, Northern, and Eastern India (IN-WE, IN-SO, IN-NO, IN-EA), Great Britain (GB), Germany (DE), France (FR), and California (US-CAL-CISO). This dataset covers an approximately 48-hour window of recent historical and forecasted hourly carbon intensity, sufficient to compare relative carbon intensity across structurally different grids at the same points in time, though shorter than the single-region temporal dataset. Job workloads were defined with durations from 2 to 10 hours and deadline windows from 8 to 36 hours, reflecting a realistic range of AI training and inference job flexibility.")]),

  h2("3.4 Scheduling Algorithm"),
  p([t("The Scheduling Decision Engine implements the following exhaustive-search algorithm:")]),
  codeLine("Algorithm: Carbon-Aware Job Scheduling"),
  codeLine(""),
  codeLine("Input: job duration d, submission time t0, deadline t_deadline,"),
  codeLine("       forecasted carbon intensity C(t, r) for candidate region(s) R"),
  codeLine("Output: selected start time t_s*, selected region r*"),
  codeLine(""),
  codeLine("1. S = { t_s : t0 <= t_s and t_s + d <= t_deadline }"),
  codeLine("2. For each region r in R, for each t_s in S:"),
  codeLine("     window_emissions(t_s, r) = sum of C(t, r) over [t_s, t_s + d]"),
  codeLine("3. (t_s*, r*) = argmin over all (t_s, r) of window_emissions(t_s, r)"),
  codeLine("4. If relocation disallowed, restrict R to job's default region."),
  codeLine("5. Hold job until t_s*, dispatch to region r*."),
  new Paragraph({ spacing: { after: 200 }, children: [] }),
  p([t("Exhaustive search is used rather than a learning-based approach because the feasible window per job is small (hours to days), making exhaustive search computationally trivial while remaining fully interpretable and auditable, a property favored in production scheduling contexts.")]),

  h2("3.5 Baseline for Comparison"),
  p([t("The carbon-agnostic baseline dispatches each job immediately at its submission time "), m("t"), sub("0"),
    t(", reflecting the default behavior of most production schedulers. The difference in emissions between the carbon-aware schedule and this baseline constitutes the carbon savings attributable to the framework; the difference in start time constitutes the added scheduling delay.")]),

  h1("4. Experimental Setup"),
  p([t("The framework described in Section 3 was implemented in Python, with the Carbon Intensity Data Module, Job Profiler, Scheduling Decision Engine, Baseline Comparator, and Dispatcher as separate modules matching Figure 1. Two experiments were run, corresponding to the two datasets described in Section 3.3.")]),
  p([t("The temporal scheduling experiment used the 21-day UK dataset. Four job configurations were defined, varying in duration (2, 4, 6, and 10 hours) and deadline window (8, 16, 24, and 36 hours respectively), each representing a different degree of scheduling flexibility. For each configuration, 100 trials were run with submission times sampled uniformly at random across the full 21-day window, giving 400 trials in total. For each trial, the Scheduling Decision Engine searched all feasible half-hourly start times within the deadline window and selected the one minimizing total forecasted emissions, which was then compared against the carbon-agnostic baseline of immediate execution at the sampled submission time.")]),
  p([t("The spatial scheduling experiment used the 48-hour, eight-region Electricity Maps dataset. Seven representative jobs, each with a fixed duration, deadline, default region, and power draw, were scheduled twice: once restricted to their default region (temporal-only), and once permitted to search across all eight regions (temporal-and-spatial). Emissions for both configurations were compared against the same carbon-agnostic baseline.")]),

  h1("5. Results and Analysis"),
  h2("5.1 Temporal Scheduling: 21-Day Real Dataset (400 Trials)"),
  p([t("Table 2 reports carbon savings and added delay for each job flexibility configuration, aggregated across 100 randomly sampled trials per configuration using the real 21-day UK carbon intensity dataset.")]),
  trialTable,
  caption("Table 2. Temporal scheduling results across 400 trials on the real 21-day UK dataset, by job flexibility configuration."),
  p([t("Carbon savings increase with job flexibility, from a mean of 21.08 percent for short jobs with an 8-hour deadline window to 32.86 percent for jobs with a 24-hour window, before plateauing at 32.41 percent for the 36-hour window configuration. This plateau suggests that, for this dataset's diurnal carbon intensity pattern, most of the achievable benefit of temporal flexibility is captured within roughly a 24-hour search window, and that further widening the deadline yields diminishing returns. The standard deviations, ranging from 19 to 23 percent, and the wide min-max ranges (0 percent to over 80 percent for the longer configurations) indicate substantial trial-to-trial variability: for some randomly sampled submission times, the job was already submitted at a near-optimal moment, while for others a large reduction was available. This variability is itself an expected and realistic property of carbon-aware scheduling, and is only visible because of the multi-trial evaluation design; a single-snapshot evaluation would report only one point on this distribution. The weighted mean carbon reduction across all 400 trials was 29.00 percent, at a weighted mean added delay of 7.95 hours.")]),

  h2("5.2 Forecast Uncertainty Sensitivity"),
  p([t("Objective 4 of this research called for evaluating the framework's sensitivity to carbon intensity forecast error. The UK NESO API reports both a forecasted and an actual carbon intensity value for each half-hourly settlement period, enabling a direct measurement of forecast error and its downstream effect on scheduling quality, using the same real 21-day dataset and 400 trials as Section 5.1.")]),
  p([t("Across all 1,008 paired settlement periods in the dataset, the forecast showed a Mean Absolute Error of 17.25 gCO2/kWh, a Root Mean Squared Error of 25.17 gCO2/kWh, a mean absolute percentage error of 18.63 percent, and a correlation of 0.82 with the actual realized carbon intensity. This represents a moderate, non-trivial level of forecast error typical of short-horizon grid forecasts.")]),
  p([t("To measure the downstream effect of this error on scheduling quality, each of the 400 trials was scheduled twice: once using only forecast data, as a real deployment would have to at decision time, with true emissions then computed using the actual realized carbon intensity for the chosen window; and once using an oracle scheduler with perfect foresight of actual carbon intensity, representing a theoretical upper bound that could never be achieved in practice. Table 3 reports the results.")]),
  forecastTable,
  caption("Table 3. Realistic forecast-based scheduling versus a perfect-foresight oracle upper bound, across the same 400 trials as Table 2, quantifying the cost of forecast uncertainty."),
  p([t("Forecast-based scheduling achieved a weighted mean carbon reduction of 24.47 percent, compared to 29.73 percent for the perfect-foresight oracle, indicating that forecast uncertainty costs approximately 5.26 percentage points of achievable carbon reduction under real deployment conditions. This cost was not uniform across configurations: it was smallest for the long configuration (6.39 percentage points) and largest for the very long configuration (11.07 percentage points), suggesting that as jobs become more flexible and the scheduler searches further into the forecast horizon, it becomes more likely to select a window where the forecast is furthest from the eventual actual value. Despite this cost, forecast-based scheduling still achieved substantially higher carbon reduction than either the carbon-agnostic baseline or the Flexible Start strategy discussed in Section 5.4, confirming that carbon-aware scheduling remains worthwhile even under realistic forecast uncertainty, though the achievable benefit is measurably smaller than an idealized analysis assuming perfect forecasts would suggest.")]),

  h2("5.4 Comparison Against a Prior Baseline Strategy"),
  p([t("To assess whether the proposed full-deadline-window search offers a meaningful improvement over an existing carbon-aware strategy from the literature, rather than only over a carbon-agnostic baseline, the same 400 trials from Section 5.1 were additionally evaluated against a Flexible Start strategy in the style of Vergallo and Mainetti [6], which searches only a short, fixed 4-hour delay window before starting the job, rather than the job's full deadline window. Table 4 reports the comparison.")]),
  baselineCompTable,
  caption("Table 4. Proposed full-deadline-window scheduling compared against a bounded 4-hour Flexible Start strategy [6], across the same 400 real-data trials."),
  p([t("The comparison reveals a pattern with direct practical significance: Flexible Start's effectiveness decreases as job flexibility increases, from 17.67 percent for short jobs to just 9.78 percent for the longest, most flexible job configuration, because a fixed 4-hour search window becomes a progressively smaller fraction of a longer deadline. The proposed full-window approach shows the opposite pattern, improving from 21.08 to 32.86 percent as flexibility increases, since it can exploit the entire deadline window rather than only its first few hours. As a result, the improvement of the proposed method over Flexible Start grows from 4.80 percentage points for short jobs to 25.18 percentage points for very long jobs, indicating that the benefit of searching the full deadline window, rather than a bounded initial window, is most pronounced precisely for the longer, more flexible jobs where bounded-window strategies are least effective. Weighted across all 400 trials, the proposed method achieves a mean carbon reduction of 29.00 percent compared to 13.26 percent for Flexible Start, a 15.74 percentage point improvement over an established prior strategy rather than only over immediate execution.")]),


  h2("5.5 Spatial Scheduling: 48-Hour, Eight-Region Dataset"),
  p([t("Table 5 reports per-job emissions and percentage carbon savings for the eight-region spatial scheduling experiment, using real Electricity Maps carbon intensity data for the 48-hour evaluation window described in Section 3.3.")]),
  resultsTable,
  caption("Table 5. Per-job baseline vs. carbon-aware scheduling emissions and savings, temporal-only and temporal-plus-spatial configurations, eight-region dataset."),
  p([t("Averaged across all seven jobs, temporal-only scheduling restricted to each job's default region achieved a mean carbon emissions reduction of 24.56 percent, consistent in magnitude with the shorter-window configurations in the 21-day temporal experiment. Allowing spatial relocation across the eight candidate regions increased the mean carbon reduction to 83.66 percent, while reducing the average added delay from 7.86 to 3.29 hours. Every job showed some improvement from spatial relocation; job-004, whose default region (Eastern India) carried the highest baseline carbon intensity in the dataset, improved from a 4.44 percent reduction under temporal-only scheduling to a 97.23 percent reduction once relocation to a cleaner grid was permitted.")]),
  p([t("A consistent pattern in the spatial results is that the scheduler routed the majority of relocatable jobs to France (FR), the region with the lowest carbon intensity across most of the evaluated window, owing to its largely nuclear generation mix. While this validates the core mechanism -- the scheduler correctly identifies and exploits the lowest-carbon available option -- it also indicates that, in a real multi-tenant deployment, spatial carbon-aware scheduling without additional load-balancing or capacity constraints could concentrate demand onto a small number of already-clean regions; this is discussed further as a limitation in Section 6.")]),
  p([t("Comparing the two experiments, spatial flexibility (83.66 percent) yields substantially larger carbon reductions than temporal flexibility alone (24.56 to 32.86 percent depending on window size), while also incurring lower added delay in the spatial case. This is consistent with the underlying mechanism: temporal shifting is bounded by the diurnal carbon intensity pattern within a single grid, whereas spatial relocation can exploit persistent structural differences between grids with very different generation mixes, which in this dataset spanned more than an order of magnitude in baseline carbon intensity between the cleanest and dirtiest regions.")]),

  h1("6. Discussion"),
  p([t("The results support the paper's central claim: carbon-aware scheduling can achieve substantial emissions reductions for AI workloads using only software-level changes. The 400-trial temporal evaluation on 21 real days shows this is not an artifact of a single favorable snapshot: mean carbon reduction ranged from 21.08 to 32.86 percent depending on job flexibility, with a plateau beyond roughly a 24-hour deadline window, a pattern that would not have been visible from a single-snapshot evaluation. The spatial evaluation further shows that combining temporal with spatial flexibility yields markedly larger reductions than temporal shifting alone: an 83.66 percent mean reduction, roughly 2.5 to 4 times larger than any temporal-only configuration, while simultaneously incurring lower added delay. This suggests that where data residency and latency constraints permit, spatial flexibility is a substantially more valuable lever than temporal flexibility alone for organizations seeking to reduce AI-related emissions.")]),
  p([t("Several limitations should be acknowledged. First, the spatial evaluation window remains approximately 48 hours; while the temporal evaluation was strengthened to a real 21-day, 400-trial analysis, extending the spatial evaluation to a comparably long multi-week window across all eight regions was not possible within this study due to API access restrictions on extended historical data for that data source, and is identified as near-term future work. Second, job power draw values for the spatial experiment were specified based on representative figures rather than measured from an actual running training job; a supplementary measurement using the CodeCarbon emissions-tracking library was performed on a small real training job (a three-layer neural network trained to 97.78 percent accuracy), yielding a measured average power draw of approximately 0.00614 kW using CPU-based estimation, since GPU hardware access was not available in the development environment. This confirms the measurement methodology is implementable and independently reproducible, but does not yet cover the larger multi-kilowatt jobs used in the spatial experiment; repeating this measurement on GPU hardware for a comparable job is identified as future work. Third, while Section 5.2 quantifies the cost of forecast uncertainty using paired forecast-versus-actual data for a single-region, short-horizon (day-ahead) forecast, the sensitivity of the framework to longer forecast horizons, such as the 24-to-96-hour forecasts often required for spatial and multi-day scheduling decisions, was not separately evaluated, since paired long-horizon forecast-versus-actual data was not available for the datasets used in this study; this remains a natural extension of the analysis already performed. Fourth, as noted in Section 5.5, unconstrained spatial relocation concentrated demand onto a single low-carbon region in the eight-region evaluation window; a production deployment would likely need additional capacity or fairness constraints to avoid overloading any single grid region, an extension not modeled in the current formulation.")]),
  p([t("Despite these limitations, the framework's practical integration path is straightforward: the Scheduling Decision Engine can sit alongside existing orchestration systems such as Kubernetes or SLURM without requiring changes to how jobs themselves are defined, consistent with the orchestration-layer integration pathways discussed in the reviewed literature [17], [18].")]),

  h1("7. Conclusion and Future Work"),
  p([t("This paper presented a Carbon-Aware AI Model Scheduling framework that determines optimal execution windows, and optionally execution regions, for AI training and inference jobs based on real and forecasted grid carbon intensity, subject to configurable deadlines. Evaluated using a real 21-day, 400-trial temporal dataset for Great Britain and a real 48-hour, eight-region spatial dataset spanning India, the United Kingdom, Germany, France, and California, the framework achieved a weighted mean carbon emissions reduction of 29.00 percent under temporal-only scheduling, rising to 32.86 percent for jobs with a 24-hour deadline window, and 83.66 percent when spatial relocation was additionally permitted. Under realistic forecast uncertainty, measured directly from paired forecast-versus-actual grid data, achievable temporal savings were found to be 24.47 percent against a 29.73 percent perfect-foresight upper bound, and the proposed full-deadline-window search was shown to outperform a bounded-window Flexible Start strategy from prior literature by 15.74 percentage points. These results address the gap identified in the literature review: an integrated, empirically evaluated scheduling framework spanning both temporal and spatial flexibility for AI-specific workloads, using real, multi-trial carbon data, an explicit accounting of forecast uncertainty, and a direct comparison against an existing scheduling strategy, rather than a single synthetic or snapshot evaluation compared only to a carbon-agnostic baseline.")]),
  p([t("Future work should extend the spatial evaluation to a multi-week data window comparable to the temporal evaluation, pending resolution of the historical-data access restrictions encountered with the eight-region data source in this study; incorporate GPU-measured, rather than specified, power draw from actual training runs, building on the CPU-based CodeCarbon measurement demonstrated in this work; extend the forecast uncertainty analysis to longer forecast horizons and to the multi-region spatial setting, building on the day-ahead, single-region sensitivity analysis performed in this work; and extend the scheduling formulation with fairness or capacity constraints to prevent unconstrained spatial relocation from concentrating demand on a small number of low-carbon regions.")]),

  h1("References"),
  refLine(1, "B. Radovanovic et al., \"Carbon-Aware Computing for Datacenters,\" IEEE Trans. Power Syst., 2021, arXiv:2106.11750."),
  refLine(2, "B. Acun et al., \"Carbon Explorer: A Holistic Approach for Designing Carbon Aware Datacenters,\" Proc. ACM ASPLOS, 2023."),
  refLine(3, "P. Wiesner, I. Behnke, K. Scheinert, K. Gontarska, and L. Thamsen, \"Let's Wait Awhile: How Temporal Workload Shifting Can Reduce Carbon Emissions in the Cloud,\" Proc. ACM Middleware, 2021, arXiv:2110.13234."),
  refLine(4, "Green Software Foundation, \"Carbon Aware SDK and Software Carbon Intensity (SCI) Specification,\" ISO/IEC 21031."),
  refLine(5, "\"Carbon-Aware Training Schedules for Machine Learning Models: An Energy-Efficient Green AI Approach,\" ResearchGate, 2026."),
  refLine(6, "A. Vergallo and L. Mainetti, \"Measuring the Effectiveness of Carbon-Aware AI Training Strategies in Cloud Instances: A Confirmation Study,\" Future Internet, vol. 16, no. 9, p. 334, 2024."),
  refLine(7, "P. Arputharaj, C. Rodriguez, G. Rodio, and G. Neglia, \"Green Federated Learning via Carbon-Aware Client and Time Slot Scheduling,\" Proc. IEEE MASCOTS, 2025, arXiv:2509.08980."),
  refLine(8, "X. Qiu, T. Parcollet et al., \"A First Look into the Carbon Footprint of Federated Learning,\" J. Mach. Learn. Res., vol. 24, no. 129, 2023."),
  refLine(9, "N. Bostandoost, J. Lechowicz, A. Hanafy, N. Bashir, P. Shenoy, and M. Hajiesmaili, \"LACS: Learning-Augmented Algorithms for Carbon-Aware Resource Scaling with Uncertain Demand,\" Proc. ACM e-Energy, 2024, arXiv:2404.15211."),
  refLine(10, "\"Carbon-Aware Compute-Power Scheduling for AI Data Centers with Microgrid Prosumer Operations,\" arXiv:2605.03751, 2026."),
  refLine(11, "\"Hierarchical Multi-Agent Reinforcement Learning for Carbon-Aware AI Data Centers in Power Distribution Systems,\" arXiv:2607.03324, 2026."),
  refLine(12, "\"Energy and Carbon-Aware Distributed Machine Learning Tasks Scheduling Scheme for the Multi-Renewable Energy-Based Edge-Cloud Continuum,\" Sci. Technol. Energy Transit., 2024."),
  refLine(13, "C. Zhang, M. Xu, W. Y. B. Lim, and D. Niyato, \"Sustainable AIGC Workload Scheduling of Geo-Distributed Data Centers,\" Proc. IEEE GLOBECOM, 2023."),
  refLine(14, "T. Rodrigues, E. Goldverg, and T. Kosar, \"LinTS: Carbon-Aware Temporal Data Transfer Scheduling Across Cloud Datacenters,\" arXiv:2506.04117, 2025."),
  refLine(15, "Y. Zhang, X. Guo, Z. Tan, Y. Sun, and C. Jiang, \"CarbonEdge: Carbon-Aware Deep Learning Inference Framework for Sustainable Edge Computing,\" arXiv:2603.27420, 2026."),
  refLine(16, "\"CarbonEdge: Leveraging Mesoscale Spatial Carbon-Intensity Variations for Low Carbon Edge Computing,\" arXiv:2502.14076, 2025."),
  refLine(17, "Y. Yang, A. Saad, D. Wu, J. Niu, V. C. M. Leung, and S. Drew, \"A Survey on Task Scheduling in Carbon-Aware Container Orchestration,\" arXiv:2508.05949, 2025."),
  refLine(18, "A. Saad et al., \"Towards Carbon-Aware Container Orchestration: Predicting Workload Energy Consumption with Federated Learning,\" arXiv:2510.03970, 2025."),
  refLine(19, "J. Lechowicz et al., \"Carbon- and Precedence-Aware Scheduling for Data Processing Clusters,\" Proc. ACM SIGCOMM, 2025, arXiv:2502.09717."),
  refLine(20, "T. West, K. Moawad, F. Lehmann, P. Bountris, U. Leser, Y. Elkhatib, and L. Thamsen, \"A Systematic Evaluation of the Potential of Carbon-Aware Execution for Scientific Workflows,\" Future Gener. Comput. Syst., vol. 182, p. 108453, 2026, arXiv:2508.14625."),
];

// ============================================================
// ASSEMBLE DOCUMENT
// ============================================================
const doc = new Document({
  sections: [
    { properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children: sectionA },
    { properties: { page: { size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE }, margin: { top: 500, bottom: 500, left: 500, right: 500 } } }, children: sectionB },
    { properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children: sectionC },
  ],
});

Packer.toBuffer(doc).then((buf) => fs.writeFileSync("/home/claude/carbon-aware-scheduler/Carbon_Aware_AI_Scheduling_Full_Paper.docx", buf));
