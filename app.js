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
const BACKEND_API_URL = "https://paper-consistency-platform-api.onrender.com";

let activeIssueId = null;
let currentIssues = [];
let currentSentences = collectInitialSentences();
let lastEngineSource = "preview";

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

function startProgressAnimation() {
  let value = 8;
  progressBar.style.width = `${value}%`;
  return setInterval(() => {
    value = Math.min(value + 11, 90);
    progressBar.style.width = `${value}%`;
  }, 220);
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
  setStatus("Uploading file and running analysis...", "Running");
  const timer = startProgressAnimation();

  try {
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
    activeIssueId = null;

    renderPaper(currentSentences);
    renderIssues();
    progressBar.style.width = "100%";
    setStatus(
      `Completed with ${lastEngineSource} engine. ${currentIssues.length} issues found.`,
      "Completed",
      true
    );
    runCheckBtn.textContent = "Run Again";
  } catch (error) {
    progressBar.style.width = "0";
    setStatus(`Analysis failed: ${error.message}`, "Failed");
    runCheckBtn.textContent = "Retry";
  } finally {
    clearInterval(timer);
    runCheckBtn.disabled = false;
  }
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

renderKpi([]);
