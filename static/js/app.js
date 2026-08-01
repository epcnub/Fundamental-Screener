/* app.js – NSE Fundamental Screener frontend */

// ── State ──────────────────────────────────────────────────
let allRows    = [];
let sortCol    = "rank";
let sortDir    = "asc";
let nameMap    = {};

// ── DOM refs ───────────────────────────────────────────────
const btnRun        = document.getElementById("btn-run");
const btnExport     = document.getElementById("btn-export");
const selUniverse   = document.getElementById("sel-universe");
const customWrap    = document.getElementById("custom-input-wrap");
const customSymbols = document.getElementById("custom-symbols");
const selGrade      = document.getElementById("sel-grade");
const selFlags      = document.getElementById("sel-flags");
const searchBox     = document.getElementById("search-box");

const emptyState    = document.getElementById("empty-state");
const loadingState  = document.getElementById("loading-state");
const loadingText   = document.getElementById("loading-text");
const resultsWrap   = document.getElementById("results-wrap");
const statsBar      = document.getElementById("stats-bar");
const tableBody     = document.getElementById("table-body");
const flagsContainer= document.getElementById("flags-container");
const gradeBars     = document.getElementById("grade-bars");

// Modal
const modalOverlay  = document.getElementById("modal-overlay");
const modalClose    = document.getElementById("modal-close");
const modalTitle    = document.getElementById("modal-title");
const modalSubtitle = document.getElementById("modal-subtitle");
const modalScore    = document.getElementById("modal-score");
const modalGrade    = document.getElementById("modal-grade");
const modalBreakdown= document.getElementById("modal-breakdown");
const modalFlagsWrap= document.getElementById("modal-flags-wrap");

// ── Helpers ────────────────────────────────────────────────
const fmt = v => (v === "—" || v === null || v === undefined) ? "—" : v;
const num = v => (v === "—" || v == null) ? null : +v;

function gradeClass(g) {
  return { A:"badge-A", B:"badge-B", C:"badge-C", D:"badge-D", F:"badge-F" }[g] || "badge-NA";
}

function scoreColor(s) {
  if (s >= 75) return "#22c55e";
  if (s >= 60) return "#86efac";
  if (s >= 45) return "#eab308";
  if (s >= 30) return "#f97316";
  return "#ef4444";
}

function gradeColorClass(g) {
  return { A:"grade-A", B:"grade-B", C:"grade-C", D:"grade-D", F:"grade-F" }[g] || "";
}

// ── Universe selector ──────────────────────────────────────
selUniverse.addEventListener("change", () => {
  customWrap.style.display = selUniverse.value === "custom" ? "flex" : "none";
});

// ── Tabs ───────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(t => t.style.display = "none");
    tab.classList.add("active");
    document.getElementById("tab-" + tab.dataset.tab).style.display = "block";
  });
});

// ── Run screener ───────────────────────────────────────────
btnRun.addEventListener("click", async () => {
  const universe = selUniverse.value;
  let symbols = null;

  if (universe === "nifty50") {
    symbols = [
      "ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK",
      "BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BPCL","BHARTIARTL",
      "BRITANNIA","CIPLA","COALINDIA","DIVISLAB","DRREDDY",
      "EICHERMOT","GRASIM","HCLTECH","HDFCBANK","HDFCLIFE",
      "HEROMOTOCO","HINDALCO","HINDUNILVR","ICICIBANK","ITC",
      "INDUSINDBK","INFY","JSWSTEEL","KOTAKBANK","LTIM",
      "LT","M&M","MARUTI","NTPC","NESTLEIND",
      "ONGC","POWERGRID","RELIANCE","SBILIFE","SBIN",
      "SHRIRAMFIN","SUNPHARMA","TCS","TATACONSUM","TATAMOTORS",
      "TATASTEEL","TECHM","TITAN","ULTRACEMCO","WIPRO"
    ];
  } else if (universe === "custom") {
    const raw = customSymbols.value.trim();
    if (!raw) { alert("Enter at least one symbol."); return; }
    symbols = raw.split(/[\s,]+/).map(s => s.trim().toUpperCase()).filter(Boolean);
  }

  const estSecs = symbols ? symbols.length * 1.3 : 2000 * 1.3;
  const estMins = Math.ceil(estSecs / 60);

  emptyState.style.display    = "none";
  resultsWrap.style.display   = "none";
  statsBar.style.display      = "none";
  loadingState.style.display  = "block";
  loadingText.textContent     = `Fetching fundamentals for ${symbols ? symbols.length : "~2000"} stocks…`;
  document.getElementById("loading-hint").textContent =
    `Estimated time: ~${estMins} minute${estMins > 1 ? "s" : ""}. Don't close this tab.`;
  btnRun.disabled    = true;
  btnExport.disabled = true;

  try {
    // 1. Kick off the background job
    const startResp = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols }),
    });
    const startData = await startResp.json();

    if (startData.status === "already_running") {
      alert("A screener run is already in progress. Please wait for it to finish.");
      btnRun.disabled = false;
      return;
    }

    // 2. Poll /api/status until done
    await pollUntilDone();

    // 3. Fetch the finished results
    const reportResp = await fetch("/api/report");
    const data = await reportResp.json();
    allRows = data.rows || [];
    renderAll(data.stats || {});
    btnExport.disabled = false;

  } catch (err) {
    loadingState.style.display = "none";
    emptyState.style.display   = "block";
    alert("Error running screener: " + err.message);
  } finally {
    btnRun.disabled = false;
  }
});

function pollUntilDone() {
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        const resp = await fetch("/api/status");
        const status = await resp.json();

        if (status.total > 0) {
          loadingText.textContent = `Fetching fundamentals… (${status.progress} / ${status.total})`;
        }

        if (!status.running) {
          clearInterval(interval);
          resolve();
        }
      } catch (err) {
        clearInterval(interval);
        reject(err);
      }
    }, 2000); // poll every 2 seconds
  });
}

// ── Export ─────────────────────────────────────────────────
btnExport.addEventListener("click", async () => {
  const resp = await fetch("/api/export");
  const data = await resp.json();
  if (data.error) { alert(data.error); return; }
  alert(`✔ Exported to:\n${data.path}`);
});

// ── Filters ────────────────────────────────────────────────
[selGrade, selFlags, searchBox].forEach(el => {
  el.addEventListener("input", () => renderTable(filteredRows()));
});

function filteredRows() {
  let rows = [...allRows];

  const grade = selGrade.value;
  if (grade) {
    const allowed = grade.split(",");
    rows = rows.filter(r => allowed.includes(r.grade));
  }

  const flags = selFlags.value;
  if (flags === "flagged") rows = rows.filter(r => r.red_flags && r.red_flags.length > 0);
  if (flags === "clean")   rows = rows.filter(r => !r.red_flags || r.red_flags.length === 0);

  const q = searchBox.value.trim().toLowerCase();
  if (q) rows = rows.filter(r =>
    r.symbol.toLowerCase().includes(q) ||
    (r.company || "").toLowerCase().includes(q)
  );

  return rows;
}

// ── Sorting ────────────────────────────────────────────────
document.querySelectorAll("th.sortable").forEach(th => {
  th.addEventListener("click", () => {
    const col = th.dataset.col;
    if (sortCol === col) {
      sortDir = sortDir === "asc" ? "desc" : "asc";
    } else {
      sortCol = col;
      sortDir = col === "grade" ? "asc" : "desc";
    }
    document.querySelectorAll("th").forEach(t => t.classList.remove("sort-asc","sort-desc"));
    th.classList.add(sortDir === "asc" ? "sort-asc" : "sort-desc");
    renderTable(filteredRows());
  });
});

function sortedRows(rows) {
  return [...rows].sort((a, b) => {
    let va = a[sortCol], vb = b[sortCol];
    // Numeric sort for numbers
    const na = num(va), nb = num(vb);
    if (na !== null && nb !== null) {
      return sortDir === "asc" ? na - nb : nb - na;
    }
    // String sort
    va = String(va ?? ""); vb = String(vb ?? "");
    return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
  });
}

// ── Render all sections ────────────────────────────────────
function renderAll(stats) {
  loadingState.style.display  = "none";
  resultsWrap.style.display   = "block";
  statsBar.style.display      = "flex";

  // Stats bar
  document.getElementById("stat-total").textContent  = stats.total  ?? "—";
  document.getElementById("stat-avg").textContent    = stats.avg    ?? "—";
  document.getElementById("stat-a").textContent      = stats.grade_counts?.A ?? 0;
  document.getElementById("stat-b").textContent      = stats.grade_counts?.B ?? 0;
  document.getElementById("stat-f").textContent      = stats.grade_counts?.F ?? 0;
  document.getElementById("stat-flags").textContent  = stats.flagged ?? 0;
  document.getElementById("stat-best").textContent   = stats.best   ?? "—";

  renderTable(filteredRows());
  renderFlagReport();
  renderGradeChart(stats.grade_counts || {});
}

// ── Table render ───────────────────────────────────────────
function renderTable(rows) {
  const sorted = sortedRows(rows);
  tableBody.innerHTML = "";

  if (sorted.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="15" style="text-align:center;padding:40px;color:var(--muted)">No stocks match filters</td></tr>`;
    return;
  }

  sorted.forEach(r => {
    const score  = num(r.score);
    const scoreBar = score !== null
      ? `<div class="score-wrap">
           <span>${score}</span>
           <div class="score-bar-bg">
             <div class="score-bar-fill" style="width:${score}%;background:${scoreColor(score)}"></div>
           </div>
         </div>`
      : `<span class="dash">—</span>`;

    const flagsHtml = r.red_flags && r.red_flags.length
      ? r.red_flags.slice(0, 2).map(f =>
          `<span class="flag-pill" title="${f}">⚠ ${f.split("—")[0].trim()}</span>`
        ).join("") + (r.red_flags.length > 2 ? `<span class="flag-pill">+${r.red_flags.length - 2}</span>` : "")
      : `<span class="no-flags">✔ None</span>`;

    const row = document.createElement("tr");
    row.innerHTML = `
      <td class="dash">${r.rank}</td>
      <td><strong style="color:#818cf8">${r.symbol}</strong></td>
      <td style="color:var(--muted);font-size:12px">${r.company || "—"}</td>
      <td>${scoreBar}</td>
      <td><span class="badge ${gradeClass(r.grade)}">${r.grade}</span></td>
      <td>${fmt(r.roe)}</td>
      <td>${fmt(r.roce)}</td>
      <td>${fmt(r.pe_ratio)}</td>
      <td>${fmt(r.pb_ratio)}</td>
      <td>${fmt(r.de_ratio)}</td>
      <td>${fmt(r.revenue_cagr_3y)}</td>
      <td>${fmt(r.profit_cagr_3y)}</td>
      <td>${fmt(r.promoter_holding_pct)}</td>
      <td>${flagsHtml}</td>
      <td><button class="btn-detail" data-sym="${r.symbol}">Details</button></td>
    `;
    tableBody.appendChild(row);
  });

  // Detail button listeners
  tableBody.querySelectorAll(".btn-detail").forEach(btn => {
    btn.addEventListener("click", () => openModal(btn.dataset.sym));
  });
}

// ── Red flag report ────────────────────────────────────────
function renderFlagReport() {
  const flagged = allRows.filter(r => r.red_flags && r.red_flags.length > 0)
    .sort((a, b) => b.red_flags.length - a.red_flags.length);

  if (!flagged.length) {
    flagsContainer.innerHTML = `<div class="no-flags-msg">✔ No red flags found across all screened stocks.</div>`;
    return;
  }

  flagsContainer.innerHTML = flagged.map(r => `
    <div class="flag-card">
      <div class="flag-card-header">
        <span class="flag-card-sym">${r.symbol}</span>
        <span class="flag-card-name">${r.company || ""}</span>
        <span class="badge ${gradeClass(r.grade)}">${r.grade}</span>
        <span class="flag-card-score">Score: ${r.score ?? "—"}</span>
      </div>
      ${r.red_flags.map(f => `
        <div class="flag-item">
          <span class="flag-arrow">▸</span>
          <span>${f}</span>
        </div>
      `).join("")}
    </div>
  `).join("");
}

// ── Grade chart ────────────────────────────────────────────
function renderGradeChart(counts) {
  const grades  = ["A", "B", "C", "D", "F"];
  const max     = Math.max(...grades.map(g => counts[g] || 0), 1);
  const maxBarH = 140;

  gradeBars.innerHTML = grades.map(g => {
    const count  = counts[g] || 0;
    const height = Math.max((count / max) * maxBarH, count > 0 ? 4 : 0);
    return `
      <div class="grade-bar-col">
        <div class="grade-bar-val ${gradeColorClass(g)}">${count}</div>
        <div class="grade-bar bar-${g}" style="height:${height}px"></div>
        <div class="grade-bar-label ${gradeColorClass(g)}">${g}</div>
      </div>
    `;
  }).join("");
}

// ── Modal ──────────────────────────────────────────────────
function openModal(sym) {
  const row = allRows.find(r => r.symbol === sym);
  if (!row) return;

  modalTitle.textContent    = row.symbol;
  modalSubtitle.textContent = row.company || "";
  modalScore.textContent    = row.score ?? "—";
  modalGrade.textContent    = row.grade ?? "—";
  modalGrade.className      = "modal-grade-val " + gradeColorClass(row.grade);

  // Breakdown by pillar
  const pillars = ["Profitability", "Growth", "Valuation", "Debt Health", "Quality"];
  const byPillar = {};
  (row.breakdown || []).forEach(c => {
    (byPillar[c.pillar] = byPillar[c.pillar] || []).push(c);
  });

  modalBreakdown.innerHTML = pillars.map(p => {
    const crs = byPillar[p] || [];
    if (!crs.length) return "";
    const pts = crs.reduce((s, c) => s + c.points, 0);
    const max = crs.reduce((s, c) => s + c.max_points, 0);
    return `
      <div class="pillar-section">
        <div class="pillar-title">${p} &nbsp;<span style="font-weight:400">${pts}/${max} pts</span></div>
        ${crs.map(c => `
          <div class="criterion-row">
            <span class="cr-tick">${c.passed ? "✅" : "❌"}</span>
            <span class="cr-name">${c.name}</span>
            <span class="cr-pts">${c.points}/${c.max_points}</span>
            <span class="cr-note">${c.note || ""}</span>
          </div>
        `).join("")}
      </div>
    `;
  }).join("");

  // Flags in modal
  if (row.red_flags && row.red_flags.length) {
    modalFlagsWrap.innerHTML = `
      <div class="modal-flags">
        <div class="modal-flags-title">⚠ Red Flags (${row.red_flags.length})</div>
        ${row.red_flags.map(f => `
          <div class="modal-flag-item"><span>▸</span><span>${f}</span></div>
        `).join("")}
      </div>
    `;
  } else {
    modalFlagsWrap.innerHTML = `<div style="margin-top:16px;color:var(--green);font-size:13px">✔ No red flags</div>`;
  }

  modalOverlay.style.display = "flex";
}

modalClose.addEventListener("click",   () => modalOverlay.style.display = "none");
modalOverlay.addEventListener("click", e => { if (e.target === modalOverlay) modalOverlay.style.display = "none"; });
document.addEventListener("keydown",   e => { if (e.key === "Escape") modalOverlay.style.display = "none"; });