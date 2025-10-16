// ====== CONFIG: point this to your partner's backend ======
const BACKEND_BASE_URL = "http://localhost:8080"; // or your Codespace URL
const ENDPOINTS = {
  // change these if your backend uses different routes
  run: "/run_scraper",          // POST { keyword?: string, urls?: string[] }
  results: "/results",          // GET -> JSON array
  downloadCsv: "/download/csv", // GET -> file
  downloadJson: "/download/json", // GET -> file
  // optional: live log/status if your backend exposes them; otherwise this is ignored
  logs: "/logs",                // GET text (optional)
  status: "/status"             // GET {state:"running|done|error"} (optional)
};
// ==========================================================

const runBtn = document.getElementById("runBtn");
const keywordEl = document.getElementById("keyword");
const logbox = document.getElementById("logbox");
const spinner = document.getElementById("spinner");
const autoscroll = document.getElementById("autoscroll");
const filterInput = document.getElementById("filterInput");
const tbody = document.querySelector("#resultsTable tbody");

let rowsCache = []; // store raw results to enable filtering/sorting
let sortState = { key: null, dir: 1 }; // 1 asc, -1 desc
let logTimer = null, statusTimer = null;

function url(p) { return BACKEND_BASE_URL.replace(/\/$/, "") + p; }

function log(msg) {
  if (logbox.textContent === "idle") logbox.textContent = "";
  logbox.textContent += `${msg}\n`;
  if (autoscroll.checked) logbox.scrollTop = logbox.scrollHeight;
}

async function safeFetch(path, opts) {
  const res = await fetch(url(path), opts);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res;
}

function showSpinner(on) { spinner.classList.toggle("hidden", !on); }

async function startRun() {
  const val = keywordEl.value.trim();
  const body = {};
  if (val.includes(",")) {
    body.urls = val.split(",").map(s => s.trim()).filter(Boolean);
  } else if (val) {
    body.keyword = val;
  }

  logbox.textContent = "";
  log("starting run…");
  showSpinner(true);

  try {
    await safeFetch(ENDPOINTS.run, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    log("run request accepted");

    // try optional status/log polling if available
    tryStartStatusPolling();
    tryStartLogPolling();

    // always poll results once after a short delay
    await wait(1200);
    await loadResults();
    log("results loaded");
  } catch (e) {
    log(`error: ${e.message}`);
  } finally {
    showSpinner(false);
  }
}

function wait(ms){ return new Promise(r=>setTimeout(r, ms)); }

async function loadResults() {
  try {
    const res = await safeFetch(ENDPOINTS.results);
    const data = await res.json();
    rowsCache = Array.isArray(data) ? data : [];
    renderTable();
  } catch (e) {
    log(`failed to load results: ${e.message}`);
  }
}

function renderTable() {
  const q = filterInput.value.trim().toLowerCase();
  let rows = rowsCache.slice();

  if (sortState.key) {
    rows.sort((a, b) => {
      const av = (a[sortState.key] ?? "").toString().toLowerCase();
      const bv = (b[sortState.key] ?? "").toString().toLowerCase();
      return sortState.dir * (av > bv ? 1 : av < bv ? -1 : 0);
    });
  }

  if (q) {
    rows = rows.filter(r =>
      Object.values(r).some(v => (v ?? "").toString().toLowerCase().includes(q))
    );
  }

  tbody.innerHTML = "";
  for (const r of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${esc(r.title)}</td>
      <td>${esc(r.author)}</td>
      <td>${esc(r.source_domain)}</td>
      <td>${esc(r.date_publish)}</td>
      <td>${r.url ? `<a href="${r.url}" target="_blank">open</a>` : ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

function esc(s){ return (s ?? "").toString().replace(/[&<>"]/g, c => ({
  "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"
}[c])); }

function handleSortClick(e){
  const th = e.target.closest("th");
  if (!th) return;
  const key = th.dataset.key;
  if (!key) return;
  if (sortState.key === key) sortState.dir *= -1;
  else { sortState.key = key; sortState.dir = 1; }
  renderTable();
}

async function download(kind) {
  // Prefer backend download endpoints if they exist
  const endpoint = kind === "csv" ? ENDPOINTS.downloadCsv : ENDPOINTS.downloadJson;
  if (endpoint) {
    window.open(url(endpoint), "_blank");
    return;
  }
  // Fallback: download client-side from current table
  if (kind === "json") {
    const blob = new Blob([JSON.stringify(rowsCache, null, 2)], { type: "application/json" });
    saveBlob(blob, "results.json");
  } else {
    const csv = toCSV(rowsCache);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    saveBlob(blob, "results.csv");
  }
}

function toCSV(rows) {
  if (!rows.length) return "";
  const keys = ["title","author","source_domain","date_publish","url"];
  const header = keys.join(",");
  const lines = rows.map(r => keys.map(k => csvCell(r[k])).join(","));
  return [header, ...lines].join("\n");
}
function csvCell(v){
  let s = (v ?? "").toString().replace(/"/g,'""');
  if (/[",\n]/.test(s)) s = `"${s}"`;
  return s;
}
function saveBlob(blob, name){
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

// optional polling (only runs if endpoints respond)
function tryStartLogPolling(){
  stopLogPolling();
  if (!ENDPOINTS.logs) return;
  logTimer = setInterval(async () => {
    try {
      const res = await fetch(url(ENDPOINTS.logs));
      if (res.ok) {
        const text = await res.text();
        logbox.textContent = text || "(no log yet)";
        if (autoscroll.checked) logbox.scrollTop = logbox.scrollHeight;
      }
    } catch {}
  }, 1500);
}
function stopLogPolling(){ if (logTimer) clearInterval(logTimer), logTimer=null; }

function tryStartStatusPolling(){
  stopStatusPolling();
  if (!ENDPOINTS.status) return;
  statusTimer = setInterval(async () => {
    try {
      const res = await fetch(url(ENDPOINTS.status));
      if (res.ok) {
        const s = await res.json();
        if (s.state === "done" || s.state === "error") {
          showSpinner(false);
          await loadResults();
          stopStatusPolling();
          stopLogPolling();
        }
      }
    } catch {}
  }, 1500);
}
function stopStatusPolling(){ if (statusTimer) clearInterval(statusTimer), statusTimer=null; }

// wire up UI
runBtn.addEventListener("click", startRun);
filterInput.addEventListener("input", renderTable);
document.querySelector("#resultsTable thead").addEventListener("click", handleSortClick);
document.getElementById("dlCsvBtn").addEventListener("click", () => download("csv"));
document.getElementById("dlJsonBtn").addEventListener("click", () => download("json"));

// initial load if results already exist
loadResults();
