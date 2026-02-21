const runCheckBtn = document.getElementById("run-check-btn");
const exportBtn = document.getElementById("export-btn");
const issueFilter = document.getElementById("issue-filter");
const issueList = document.getElementById("issue-list");
const issueCount = document.getElementById("issue-count");
const progressBar = document.getElementById("progress-bar");
const statusBadge = document.getElementById("status-badge");
const statusMessage = document.getElementById("status-message");
const selectedFile = document.getElementById("selected-file");
const paperFileInput = document.getElementById("paper-file");
const pickFileBtn = document.getElementById("pick-file-btn");
const kpiTotal = document.getElementById("kpi-total");
const kpiHigh = document.getElementById("kpi-high");
const kpiMedium = document.getElementById("kpi-medium");
const kpiLow = document.getElementById("kpi-low");
const paperView = document.getElementById("paper-view");
const glmBaseUrlInput = document.getElementById("glm-base-url");
const glmModelInput = document.getElementById("glm-model");
const glmApiKeyInput = document.getElementById("glm-api-key");
const engineDetail = document.getElementById("engine-detail");
const demoPdfBtn = document.getElementById("demo-pdf-btn");
const demoWordBtn = document.getElementById("demo-word-btn");
const demoLatexBtn = document.getElementById("demo-latex-btn");
const debugLine = document.getElementById("debug-line");
const APP_BUILD = "2026-02-21.5";
const BACKEND_API_URL = "https://paper-consistency-platform-api.onrender.com";

let activeIssueId = null;
let currentIssues = [];
let currentSentences = collectInitialSentences();
let lastEngineSource = "preview";
let lastEngineInfo = { glm_attempted: false, glm_used: false };

const DEMO_DATASETS = {
  pdf: {
    label: "PDF Demo",
    sentences: [
      {
        id: "s-1",
        text: "Section 2 defines the key metric as threshold voltage window for all experiments."
      },
      {
        id: "s-2",
        text: "Figure 4 reports improved robustness under high-temperature stress."
      },
      {
        id: "s-3",
        text: "Section 3 renames the same metric as switching threshold bandwidth."
      }
    ],
    issues: [
      {
        id: "d-pdf-1",
        type: "term",
        severity: "medium",
        sentenceId: "s-3",
        title: "Terminology Drift",
        detail: "The metric name changes from threshold voltage window to switching threshold bandwidth."
      }
    ]
  },
  word: {
    label: "Word Demo",
    sentences: [
      {
        id: "s-1",
        text: "The draft claims the model stability increases from 25C to 85C."
      },
      {
        id: "s-2",
        text: "In the discussion chapter, the same experiment is described as decreasing stability at 85C."
      },
      {
        id: "s-3",
        text: "The contradiction appears in two adjacent subsections."
      }
    ],
    issues: [
      {
        id: "d-word-1",
        type: "logic",
        severity: "high",
        sentenceId: "s-2",
        title: "Logic Conflict",
        detail: "The trend of stability is opposite between method and discussion sections."
      }
    ]
  },
  latex: {
    label: "LaTeX Demo",
    sentences: [
      {
        id: "s-1",
        text: "Figure 7 caption states that the read window shrinks at high temperature."
      },
      {
        id: "s-2",
        text: "The main paragraph above Figure 7 says the read window expands under the same condition."
      },
      {
        id: "s-3",
        text: "Equation (9) remains unchanged and does not support expansion."
      }
    ],
    issues: [
      {
        id: "d-latex-1",
        type: "citation_figure",
        severity: "high",
        sentenceId: "s-2",
        title: "Figure/Text Mismatch",
        detail: "Figure caption and main text describe opposite read-window behavior."
      }
    ]
  }
};

function collectInitialSentences() {
  const nodes = Array.from(document.querySelectorAll("[data-sentence-id]"));
  return nodes.map((node) => ({ id: node.dataset.sentenceId, text: node.textContent.trim() }));
}

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function severityLabel(level) {
  if (level === "high") return "High Risk";
  if (level === "medium") return "Medium Risk";
  return "Low Risk";
}

function typeLabel(type) {
  if (type === "term") return "Terminology";
  if (type === "logic") return "Logic";
  return "Citation/Figure";
}

function normalizeIssues(rawIssues) {
  return (rawIssues || []).map((issue, idx) => {
    const type = ["term", "logic", "citation_figure"].includes(issue.type) ? issue.type : "logic";
    const severity = ["low", "medium", "high"].includes(issue.severity) ? issue.severity : "medium";
    return {
      id: issue.id || `issue-${idx + 1}`,
      type,
      severity,
      sentenceId: issue.sentence_id || issue.sentenceId || `s-${idx + 1}`,
      title: issue.title || "Detected Issue",
      detail: issue.detail || "No detailed explanation provided."
    };
  });
}

function normalizeSentences(rawSentences) {
  return (rawSentences || [])
    .map((item, idx) => {
      if (typeof item === "string") {
        return { id: `s-${idx + 1}`, text: item };
      }
      return {
        id: item.id || `s-${idx + 1}`,
        text: item.text || ""
      };
    })
    .filter((item) => item.text.trim().length > 0);
}

function clearHighlight() {
  document.querySelectorAll("[data-sentence-id]").forEach((el) => {
    el.classList.remove("highlight");
  });
}

function highlightSentence(sentenceId) {
  clearHighlight();
  const target = document.querySelector(`[data-sentence-id="${sentenceId}"]`);
  if (!target) return;
  target.classList.add("highlight");
  target.scrollIntoView({ behavior: "smooth", block: "center" });
}

function renderPaper(sentences) {
  if (!sentences.length) {
    paperView.innerHTML = '<p class="muted">No extracted sentences available.</p>';
    return;
  }

  const blocks = sentences
    .map(
      (item) =>
        `<p data-sentence-id="${escapeHtml(item.id)}">${escapeHtml(item.text)}</p>`
    )
    .join("");
  paperView.innerHTML = `<h3>Extracted Sentences</h3>${blocks}`;
}

function renderKpi(displayIssues) {
  const high = displayIssues.filter((x) => x.severity === "high").length;
  const medium = displayIssues.filter((x) => x.severity === "medium").length;
  const low = displayIssues.filter((x) => x.severity === "low").length;

  kpiTotal.textContent = String(displayIssues.length);
  kpiHigh.textContent = String(high);
  kpiMedium.textContent = String(medium);
  kpiLow.textContent = String(low);
}

function renderIssues() {
  const filter = issueFilter.value;
  const displayIssues =
    filter === "all" ? currentIssues : currentIssues.filter((x) => x.type === filter);

  issueList.innerHTML = "";
  issueCount.textContent = `${displayIssues.length} items`;
  renderKpi(displayIssues);

  if (!displayIssues.length) {
    const empty = document.createElement("li");
    empty.className = "muted";
    empty.textContent = "No issues under the current filter.";
    issueList.appendChild(empty);
    clearHighlight();
    return;
  }

  displayIssues.forEach((item) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "issue-item";
    if (activeIssueId === item.id) {
      btn.classList.add("active");
    }
    btn.dataset.issueId = item.id;
    btn.innerHTML = `
      <div class="issue-meta">
        <span class="chip ${item.type}">${typeLabel(item.type)}</span>
        <span class="severity ${item.severity}">${severityLabel(item.severity)}</span>
      </div>
      <strong>${escapeHtml(item.title)}</strong>
      <p class="muted">${escapeHtml(item.detail)}</p>
      <small class="muted">Sentence ID: ${escapeHtml(item.sentenceId)}</small>
    `;
    btn.addEventListener("click", () => {
      activeIssueId = item.id;
      renderIssues();
      highlightSentence(item.sentenceId);
    });
    li.appendChild(btn);
    issueList.appendChild(li);
  });

  if (!activeIssueId) {
    activeIssueId = displayIssues[0].id;
    highlightSentence(displayIssues[0].sentenceId);
    renderIssues();
  }
}

function setStatus(text, badgeText, isSuccess = false) {
  statusMessage.textContent = text;
  statusBadge.textContent = badgeText;
  statusBadge.classList.toggle("badge-success", isSuccess);
}

function setDebugLine(text) {
  if (!debugLine) return;
  debugLine.textContent = text;
}

function renderEngineDetail(engineInfo, sourceLabel) {
  const source = sourceLabel || "heuristic";
  const attemptedRaw =
    engineInfo && Object.prototype.hasOwnProperty.call(engineInfo, "glm_attempted")
      ? engineInfo.glm_attempted
      : engineInfo && Object.prototype.hasOwnProperty.call(engineInfo, "glm_enabled")
        ? engineInfo.glm_enabled
        : null;
  const usedRaw =
    engineInfo && Object.prototype.hasOwnProperty.call(engineInfo, "glm_used")
      ? engineInfo.glm_used
      : null;

  const attemptedText =
    attemptedRaw === null || typeof attemptedRaw === "undefined"
      ? "Pending"
      : attemptedRaw
        ? "Yes"
        : "No";
  const usedText =
    usedRaw === null || typeof usedRaw === "undefined" ? "Pending" : usedRaw ? "Yes" : "No";

  let modeText = "Heuristic";
  if (source === "hybrid") {
    modeText = "Hybrid";
  } else if (source === "preview") {
    modeText = "Preview";
  } else if (source === "running") {
    modeText = "Running";
  } else if (source === "failed") {
    modeText = "Failed";
  }

  engineDetail.textContent = `Engine: ${modeText}. AI called: ${attemptedText}. AI issues used: ${usedText}.`;
}

function startProgressAnimation() {
  let value = 8;
  progressBar.style.width = `${value}%`;
  return setInterval(() => {
    value = Math.min(value + 11, 90);
    progressBar.style.width = `${value}%`;
  }, 220);
}

async function checkBackendHealth(backendUrl) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(`${backendUrl}/health`, {
      method: "GET",
      signal: controller.signal
    });
    if (!response.ok) {
      throw new Error(`health check status ${response.status}`);
    }
  } catch (error) {
    throw new Error(`Cannot connect backend (${backendUrl}): ${error.message || "unknown error"}`);
  } finally {
    clearTimeout(timer);
  }
}

async function runAnalysis() {
  const file = paperFileInput.files && paperFileInput.files[0];
  if (!file) {
    setStatus("Please choose a file before running analysis.", "Missing File");
    return;
  }

  const backendUrl = BACKEND_API_URL;

  runCheckBtn.disabled = true;
  runCheckBtn.textContent = "Running...";
  setStatus("Checking backend and uploading file...", "Running");
  renderEngineDetail({}, "running");
  setDebugLine(`Build: ${APP_BUILD} | Backend: ${backendUrl}`);
  const timer = startProgressAnimation();

  try {
    await checkBackendHealth(backendUrl);
    setStatus("Uploading file and running analysis...", "Running");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("base_url", glmBaseUrlInput.value.trim());
    formData.append("model", glmModelInput.value.trim());
    const inlineApiKey = glmApiKeyInput.value.trim();
    if (inlineApiKey) {
      formData.append("api_key", inlineApiKey);
    }

    const response = await fetch(`${backendUrl}/api/analyze`, {
      method: "POST",
      body: formData
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Request failed with status ${response.status}.`);
    }

    currentSentences = normalizeSentences(payload.sentences);
    currentIssues = normalizeIssues(payload.issues);
    lastEngineSource = payload.source || "heuristic";
    lastEngineInfo = payload.engine || {};
    activeIssueId = null;

    renderPaper(currentSentences);
    renderIssues();
    renderEngineDetail(lastEngineInfo, lastEngineSource);
    const glmErrorText =
      lastEngineInfo && lastEngineInfo.glm_error ? ` | GLM error: ${lastEngineInfo.glm_error}` : "";
    const glmInputText =
      lastEngineInfo && lastEngineInfo.glm_input_sentences
        ? ` | GLM input sentences: ${lastEngineInfo.glm_input_sentences}`
        : "";
    setDebugLine(
      `Build: ${APP_BUILD} | Backend: ${backendUrl} | Engine source: ${lastEngineSource} | AI called: ${lastEngineInfo.glm_attempted ? "Yes" : "No"}${glmInputText}${glmErrorText}`
    );
    progressBar.style.width = "100%";
    setStatus(
      `Completed with ${lastEngineSource} engine. ${currentIssues.length} issues found.`,
      "Completed",
      true
    );
    runCheckBtn.textContent = "Run Again";
  } catch (error) {
    progressBar.style.width = "0";
    const detail = error && error.message ? error.message : "unknown error";
    setStatus(`Analysis failed: ${detail}`, "Failed");
    renderEngineDetail(lastEngineInfo, "failed");
    setDebugLine(`Build: ${APP_BUILD} | Backend: ${backendUrl} | Error: ${detail}`);
    runCheckBtn.textContent = "Retry";
  } finally {
    clearInterval(timer);
    runCheckBtn.disabled = false;
  }
}

function loadDemo(kind) {
  const dataset = DEMO_DATASETS[kind];
  if (!dataset) {
    return;
  }

  currentSentences = dataset.sentences.map((item) => ({ ...item }));
  currentIssues = dataset.issues.map((item) => ({ ...item }));
  lastEngineSource = "preview";
  lastEngineInfo = { glm_attempted: false, glm_used: false };
  activeIssueId = null;

  renderPaper(currentSentences);
  renderIssues();
  progressBar.style.width = "100%";
  setStatus(`${dataset.label} loaded. Upload your file to run real analysis.`, "Demo Loaded", true);
  renderEngineDetail(lastEngineInfo, lastEngineSource);
}

function exportReport() {
  const now = new Date();
  const lines = [
    "# Consistency Check Report",
    "",
    `Generated at: ${now.toLocaleString()}`,
    `Engine source: ${lastEngineSource}`,
    `Total issues: ${currentIssues.length}`,
    "",
    "## Issue Details"
  ];

  currentIssues.forEach((item, index) => {
    lines.push(
      `${index + 1}. [${typeLabel(item.type)} | ${severityLabel(item.severity)}] ${item.title}`
    );
    lines.push(`   - Sentence ID: ${item.sentenceId}`);
    lines.push(`   - Description: ${item.detail}`);
  });

  lines.push("", "## Sentences");
  currentSentences.forEach((item) => {
    lines.push(`- ${item.id}: ${item.text}`);
  });

  const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "paper-consistency-report.md";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

paperFileInput.addEventListener("change", (event) => {
  const file = event.target.files && event.target.files[0];
  selectedFile.textContent = file ? `Selected: ${file.name}` : "No file selected";
});

pickFileBtn.addEventListener("click", () => {
  paperFileInput.click();
});

runCheckBtn.addEventListener("click", runAnalysis);
exportBtn.addEventListener("click", exportReport);
issueFilter.addEventListener("change", () => {
  activeIssueId = null;
  renderIssues();
});
demoPdfBtn.addEventListener("click", () => loadDemo("pdf"));
demoWordBtn.addEventListener("click", () => loadDemo("word"));
demoLatexBtn.addEventListener("click", () => loadDemo("latex"));

renderKpi([]);
renderEngineDetail(lastEngineInfo, lastEngineSource);
setDebugLine(`Build: ${APP_BUILD} | Backend: ${BACKEND_API_URL}`);
