const form = document.getElementById("analyze-form");
const fileInput = document.getElementById("audio-file");
const apiKeyInput = document.getElementById("api-key");
const submitButton = document.getElementById("submit-button");
const refreshHistoryButton = document.getElementById("refresh-history");
const applyHistoryFiltersButton = document.getElementById("apply-history-filters");
const loadMoreHistoryButton = document.getElementById("load-more-history");
const statusNode = document.getElementById("status");
const resultCard = document.getElementById("result-card");
const resultTitle = document.getElementById("result-title");
const resultMeta = document.getElementById("result-meta");
const resultSummary = document.getElementById("result-summary");
const historyQueryInput = document.getElementById("history-query");
const historyHasQualityInput = document.getElementById("history-has-quality");
const historyMetaNode = document.getElementById("history-meta");
const recentAnalysesNode = document.getElementById("recent-analyses");
const transcriptOutput = document.getElementById("transcript-output");
const classificationOutput = document.getElementById("classification-output");
const metricsOutput = document.getElementById("metrics-output");
const qualityOutput = document.getElementById("quality-output");

let selectedResultId = null;
const historyState = {
  items: [],
  query: "",
  hasQuality: false,
  offset: 0,
  limit: 8,
  hasMore: false,
};

function setStatus(message, type = "idle") {
  statusNode.textContent = message;
  statusNode.dataset.state = type;
}

function pretty(value) {
  if (value === null || value === undefined) {
    return "Нет данных";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}

function buildHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  if (apiKeyInput.value.trim()) {
    headers["X-API-Key"] = apiKeyInput.value.trim();
  }
  return headers;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: buildHeaders(options.headers || {}),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Ошибка запроса");
  }

  return data;
}

function renderAnalysisDetail(data) {
  selectedResultId = data.result_id;
  resultCard.classList.remove("hidden");
  resultTitle.textContent = `Результат: ${data.filename}`;

  const qualityScore = data.quality?.overall_score;
  const qualityText =
    qualityScore === undefined || qualityScore === null
      ? "без quality score"
      : `quality ${qualityScore}`;

  resultMeta.textContent = [
    data.processed_at ? `Сохранён: ${data.processed_at}` : null,
    `ID: ${data.result_id}`,
    qualityText,
  ]
    .filter(Boolean)
    .join(" · ");

  transcriptOutput.textContent = pretty(data.cleaned_text);
  classificationOutput.textContent = pretty(data.classification);
  metricsOutput.textContent = pretty(data.asr_metrics);
  qualityOutput.textContent = pretty(data.quality);
  renderDetailSummary(data);
}

function renderDetailSummary(data) {
  const summary = data.summary || {};
  const cards = [
    {
      label: "Quality score",
      value:
        summary.overall_score === undefined || summary.overall_score === null
          ? "Нет"
          : String(summary.overall_score),
      subvalue: `${summary.strengths_count || 0} strengths · ${summary.weaknesses_count || 0} weaknesses`,
    },
    {
      label: "Тип",
      value: summary.classification_type || "Не определён",
      subvalue: "Из classification metadata",
    },
    {
      label: "Артефакты",
      value: [
        summary.artifacts?.has_transcript ? "txt" : null,
        summary.artifacts?.has_metadata ? "meta" : null,
        summary.artifacts?.has_quality ? "quality" : null,
      ]
        .filter(Boolean)
        .join(" / ") || "Нет",
      subvalue: "Что уже сохранено на диске",
    },
  ];

  resultSummary.innerHTML = cards
    .map(
      (card) => `
        <article class="summary-card">
          <div class="summary-card__label">${card.label}</div>
          <div class="summary-card__value">${card.value}</div>
          <div class="summary-card__subvalue">${card.subvalue}</div>
        </article>
      `,
    )
    .join("");
}

function renderRecentAnalyses(items) {
  if (!items.length) {
    recentAnalysesNode.innerHTML =
      '<p class="empty-state">Пока нет сохранённых анализов. Загрузите первый файл.</p>';
    return;
  }

  recentAnalysesNode.innerHTML = items
    .map((item) => {
      const qualityScore =
        item.quality_summary?.overall_score === undefined ||
        item.quality_summary?.overall_score === null
          ? "без quality"
          : `score ${item.quality_summary.overall_score}`;

      const artifactBadges = [
        item.artifacts.has_transcript ? "txt" : null,
        item.artifacts.has_metadata ? "meta" : null,
        item.artifacts.has_quality ? "quality" : null,
      ]
        .filter(Boolean)
        .map((label) => `<span class="artifact-pill">${label}</span>`)
        .join("");

      const selectedClass = item.result_id === selectedResultId ? " selected" : "";

      return `
        <button class="history-item${selectedClass}" type="button" data-result-id="${item.result_id}">
          <span class="history-item__title">${item.filename}</span>
          <span class="history-item__meta">${item.processed_at || "Время неизвестно"}</span>
          <span class="history-item__meta">${qualityScore}</span>
          <span class="history-item__preview">${item.transcript_preview || "Нет транскрипта"}</span>
          <span class="artifact-row">${artifactBadges}</span>
        </button>
      `;
    })
    .join("");
}

async function loadAnalysisDetail(resultId, { updateStatus = true } = {}) {
  const data = await fetchJson(`/analyses/${encodeURIComponent(resultId)}`);
  renderAnalysisDetail(data);
  await loadRecentAnalyses({
    preferredResultId: data.result_id,
    updateStatus: false,
    reset: true,
  });

  if (updateStatus) {
    setStatus(`Открыт анализ: ${data.filename}`, "success");
  }
}

async function loadRecentAnalyses(
  {
    preferredResultId = null,
    autoloadFirst = false,
    updateStatus = true,
    reset = false,
  } = {},
) {
  if (reset) {
    historyState.offset = 0;
    historyState.items = [];
  }

  const params = new URLSearchParams({
    limit: String(historyState.limit),
    offset: String(historyState.offset),
  });

  if (historyState.query.trim()) {
    params.set("query", historyState.query.trim());
  }
  if (historyState.hasQuality) {
    params.set("has_quality", "true");
  }

  const data = await fetchJson(`/analyses?${params.toString()}`);
  if (preferredResultId) {
    selectedResultId = preferredResultId;
  }

  historyState.items = reset ? data.items : historyState.items.concat(data.items);
  historyState.offset = data.next_offset || historyState.items.length;
  historyState.hasMore = data.has_more;

  renderRecentAnalyses(historyState.items);
  renderHistoryMeta(data.total_count);
  loadMoreHistoryButton.classList.toggle("hidden", !historyState.hasMore);

  if (autoloadFirst && historyState.items.length > 0) {
    await loadAnalysisDetail(historyState.items[0].result_id, { updateStatus: false });
    return;
  }

  if (updateStatus) {
    setStatus(`История: ${data.total_count} результатов`, "idle");
  }
}

function renderHistoryMeta(totalCount) {
  const parts = [`Найдено результатов: ${totalCount}`];
  if (historyState.query.trim()) {
    parts.push(`по запросу "${historyState.query.trim()}"`);
  }
  if (historyState.hasQuality) {
    parts.push("только с quality");
  }
  historyMetaNode.textContent = parts.join(" · ");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!fileInput.files || fileInput.files.length === 0) {
    setStatus("Сначала выберите аудиофайл", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  submitButton.disabled = true;
  resultCard.classList.add("hidden");
  setStatus("Идёт анализ файла. Это может занять некоторое время.", "loading");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: buildHeaders(),
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Ошибка анализа");
    }

    renderAnalysisDetail(data);
    await loadRecentAnalyses({
      preferredResultId: data.result_id,
      updateStatus: false,
      reset: true,
    });
    setStatus(`Готово: ${data.filename}`, "success");
  } catch (error) {
    setStatus(`Ошибка: ${error.message}`, "error");
  } finally {
    submitButton.disabled = false;
  }
});

refreshHistoryButton.addEventListener("click", async () => {
  refreshHistoryButton.disabled = true;
  setStatus("Обновляю список последних анализов.", "loading");

  try {
    await loadRecentAnalyses({ reset: true });
  } catch (error) {
    setStatus(`Ошибка: ${error.message}`, "error");
  } finally {
    refreshHistoryButton.disabled = false;
  }
});

applyHistoryFiltersButton.addEventListener("click", async () => {
  applyHistoryFiltersButton.disabled = true;
  historyState.query = historyQueryInput.value;
  historyState.hasQuality = historyHasQualityInput.checked;
  setStatus("Применяю фильтры к истории.", "loading");

  try {
    await loadRecentAnalyses({ reset: true });
  } catch (error) {
    setStatus(`Ошибка: ${error.message}`, "error");
  } finally {
    applyHistoryFiltersButton.disabled = false;
  }
});

loadMoreHistoryButton.addEventListener("click", async () => {
  loadMoreHistoryButton.disabled = true;
  setStatus("Загружаю ещё результаты.", "loading");

  try {
    await loadRecentAnalyses({ reset: false });
  } catch (error) {
    setStatus(`Ошибка: ${error.message}`, "error");
  } finally {
    loadMoreHistoryButton.disabled = false;
  }
});

recentAnalysesNode.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-result-id]");
  if (!button) {
    return;
  }

  setStatus("Загружаю сохранённый анализ.", "loading");
  try {
    await loadAnalysisDetail(button.dataset.resultId);
  } catch (error) {
    setStatus(`Ошибка: ${error.message}`, "error");
  }
});

loadRecentAnalyses({ autoloadFirst: true }).catch((error) => {
  setStatus(`Ошибка: ${error.message}`, "error");
});
