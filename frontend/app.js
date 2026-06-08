const statusEl = document.querySelector("#status");
const newsCountEl = document.querySelector("#newsCount");
const reportCountEl = document.querySelector("#reportCount");
const activeReportEl = document.querySelector("#activeReport");
const validationStateEl = document.querySelector("#validationState");
const newsListEl = document.querySelector("#newsList");
const reportSelectEl = document.querySelector("#reportSelect");
const sourceListEl = document.querySelector("#sourceList");
const crawlStartDateEl = document.querySelector("#crawlStartDate");
const crawlEndDateEl = document.querySelector("#crawlEndDate");
const reportDateEl = document.querySelector("#reportDate");
const maxItemsEl = document.querySelector("#maxItems");
const summaryView = document.querySelector("#summaryView");
const markdownView = document.querySelector("#markdownView");
const jsonView = document.querySelector("#jsonView");

function today() {
  return new Date().toISOString().slice(0, 10);
}

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok || data.error) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

function postJson(path, payload) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function safeUrl(value) {
  const url = String(value ?? "").trim();
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  return "#";
}

async function loadSources() {
  const data = await api("/api/sources");
  sourceListEl.innerHTML = data.items.map((source) => `
    <label class="sourceOption">
      <input type="checkbox" value="${escapeHtml(source.id)}" checked>
      <span>${escapeHtml(source.name)}</span>
      <em>${escapeHtml(source.language)} · ${escapeHtml(source.source_type)}</em>
    </label>
  `).join("");
}

function selectedSourceIds() {
  return Array.from(sourceListEl.querySelectorAll("input[type='checkbox']:checked"))
    .map((item) => item.value);
}

async function loadNews() {
  const date = reportDateEl.value;
  const path = date ? `/api/news?limit=80&date=${encodeURIComponent(date)}` : "/api/news?limit=80";
  const data = await api(path);
  newsCountEl.textContent = data.items.length;
  newsListEl.innerHTML = data.items.map((item) => `
    <article class="newsItem">
      <h3>
        <a class="newsLink" href="${escapeHtml(safeUrl(item.url))}" target="_blank" rel="noopener noreferrer">
          ${escapeHtml(item.title)}
        </a>
      </h3>
      <p class="meta">${escapeHtml(item.source)} · ${escapeHtml(item.published_at)} · ${escapeHtml(item.source_type)}</p>
      <p>${escapeHtml(item.content).slice(0, 180)}</p>
    </article>
  `).join("") || "<p class='meta'>暂无新闻。请选择来源和日期后点击“爬取新闻”。</p>";
}

async function loadReports() {
  const data = await api("/api/reports");
  reportCountEl.textContent = data.items.length;
  reportSelectEl.innerHTML = data.items.map((item) => (
    `<option value="${item.id}">#${item.id} ${escapeHtml(item.report_date)} · ${escapeHtml(item.created_at)}</option>`
  )).join("");
  if (data.items.length) {
    await loadReport(data.items[0].id);
  } else {
    activeReportEl.textContent = "-";
    validationStateEl.textContent = "-";
    summaryView.innerHTML = "<p class='meta'>暂无日报，请先选择日期生成。</p>";
    markdownView.textContent = "";
    jsonView.textContent = "";
  }
}

async function loadReport(id) {
  const data = await api(`/api/reports/${id}`);
  activeReportEl.textContent = `#${data.id}`;
  validationStateEl.textContent = data.validation.valid ? "通过" : "需检查";
  renderSummary(data);
  markdownView.textContent = data.markdown;
  jsonView.textContent = JSON.stringify(data.report, null, 2);
}

function renderSummary(data) {
  const report = data.report;
  const hotspots = report.hotspots || [];
  const trends = report.trends || [];
  const risks = report.risk_opportunity?.risks || [];
  const opportunities = report.risk_opportunity?.opportunities || [];

  summaryView.innerHTML = `
    <section class="section">
      <h3>数据概览</h3>
      <div class="cardGrid">
        <div class="miniCard"><strong>${escapeHtml(report.report_date)}</strong><span>日报日期</span></div>
        <div class="miniCard"><strong>${report.summary.news_count}</strong><span>新闻样本</span></div>
        <div class="miniCard"><strong>${report.summary.average_impact_score}</strong><span>平均影响分</span></div>
        <div class="miniCard"><strong>${Object.keys(report.summary.event_type_count).length}</strong><span>事件类型</span></div>
      </div>
    </section>
    <section class="section">
      <h3>今日主要热点</h3>
      <div class="cardGrid">
        ${hotspots.map((item) => `
          <div class="miniCard">
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.reason)}</p>
          </div>
        `).join("")}
      </div>
    </section>
    <section class="section">
      <h3>趋势判断</h3>
      ${trends.map((item) => `
        <div class="miniCard">
          <strong>${escapeHtml(item.dimension)} · ${escapeHtml(item.confidence)}</strong>
          <p>${escapeHtml(item.insight)}</p>
        </div>
      `).join("")}
    </section>
    <section class="section">
      <h3>风险与机会</h3>
      <div class="cardGrid">
        ${risks.map((item) => `
          <div class="miniCard">
            <strong>风险 · ${escapeHtml(item.level)} · ${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.detail)}</p>
          </div>
        `).join("")}
        ${opportunities.map((item) => `
          <div class="miniCard">
            <strong>机会 · ${escapeHtml(item.level)} · ${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.detail)}</p>
          </div>
        `).join("")}
      </div>
    </section>
  `;
}

async function crawl() {
  const sourceIds = selectedSourceIds();
  if (!sourceIds.length) {
    throw new Error("请至少选择一个新闻来源");
  }
  setStatus("正在按来源和日期爬取新闻...");
  const result = await postJson("/api/crawl", {
    source_ids: sourceIds,
    start_date: crawlStartDateEl.value || null,
    end_date: crawlEndDateEl.value || null,
    max_items_per_feed: Number(maxItemsEl.value || 8),
  });
  setStatus(`爬取完成：抓取 ${result.fetched} 条，通过筛选 ${result.passed_filter} 条，过滤 ${result.filtered_out} 条，新增 ${result.inserted} 条`);
  await loadNews();
}

async function generateReport() {
  if (!reportDateEl.value) {
    throw new Error("请选择日报日期");
  }
  setStatus(`正在调用 DeepSeek 生成 ${reportDateEl.value} 日报...`);
  const result = await postJson("/api/reports/generate", {
    report_date: reportDateEl.value,
  });
  setStatus(`日报生成完成：#${result.id}`);
  await loadReports();
  reportSelectEl.value = String(result.id);
  await loadReport(result.id);
}

async function refreshAll() {
  setStatus("正在刷新...");
  await loadSources();
  await loadNews();
  await loadReports();
  setStatus("刷新完成");
}

document.querySelector("#crawlBtn").addEventListener("click", () => {
  crawl().catch((error) => setStatus(error.message, true));
});

document.querySelector("#generateBtn").addEventListener("click", () => {
  generateReport().catch((error) => setStatus(error.message, true));
});

document.querySelector("#refreshBtn").addEventListener("click", () => {
  refreshAll().catch((error) => setStatus(error.message, true));
});

reportSelectEl.addEventListener("change", (event) => {
  loadReport(event.target.value).catch((error) => setStatus(error.message, true));
});

reportDateEl.addEventListener("change", () => {
  loadNews().catch((error) => setStatus(error.message, true));
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    const active = button.dataset.tab;
    summaryView.classList.toggle("hidden", active !== "summary");
    markdownView.classList.toggle("hidden", active !== "markdown");
    jsonView.classList.toggle("hidden", active !== "json");
  });
});

crawlEndDateEl.value = today();
reportDateEl.value = today();
refreshAll().catch((error) => setStatus(error.message, true));
