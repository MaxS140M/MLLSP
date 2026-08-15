const API_BASE = "http://127.0.0.1:8000";
const state = { chart: null };

// Cache the page controls used by the dashboard.
const elements = {
  symbol: document.querySelector("#symbol"),
  refresh: document.querySelector("#refresh"),
  loading: document.querySelector("#loading"),
  error: document.querySelector("#error"),
  status: document.querySelector("#api-status"),
  statusDot: document.querySelector("#status-dot"),
  company: document.querySelector("#company"),
  ticker: document.querySelector("#ticker"),
  price: document.querySelector("#price"),
  quoteTime: document.querySelector("#quote-time"),
  prediction: document.querySelector("#prediction"),
  current: document.querySelector("#prediction-current"),
  horizon: document.querySelector("#horizon"),
  model: document.querySelector("#model"),
  updated: document.querySelector("#updated"),
  pointCount: document.querySelector("#point-count"),
  chart: document.querySelector("#price-chart"),
  emptyChart: document.querySelector("#empty-chart"),
  runAnalysis: document.querySelector("#run-analysis"),
  analysisLoading: document.querySelector("#analysis-loading"),
  analysisError: document.querySelector("#analysis-error"),
  notebookContainer: document.querySelector("#notebook-container"),
  analysisSymbol: document.querySelector("#analysis-symbol"),
  customSymbol: document.querySelector("#custom-symbol"),
  addSymbol: document.querySelector("#add-symbol"),
  addSymbolStatus: document.querySelector("#add-symbol-status"),
};

async function getJson(path) {
  // Convert API responses into usable data or clear errors.
  const response = await fetch(`${API_BASE}${path}`);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
  return payload;
}

function setLoading(isLoading) {
  elements.loading.hidden = !isLoading;
  elements.refresh.disabled = isLoading;
}

function showError(message) {
  elements.error.textContent = message;
  elements.error.hidden = false;
}

function clearError() {
  elements.error.hidden = true;
}

function formatPrice(value) {
  return Number(value).toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function renderQuote(quote) {
  // Display the latest company and price information.
  elements.company.textContent = quote.company || quote.symbol;
  elements.ticker.textContent = quote.symbol;
  elements.price.textContent = formatPrice(quote.price);
  elements.quoteTime.textContent = quote.timestamp ? `As of ${new Date(quote.timestamp).toLocaleString()}` : "Timestamp unavailable";
}

function renderPrediction(prediction) {
  // Display the saved model's next-close estimate.
  elements.prediction.textContent = formatPrice(prediction.predicted_price);
  elements.current.textContent = formatPrice(prediction.current_price);
  elements.horizon.textContent = `${prediction.horizon} period${prediction.horizon === 1 ? "" : "s"}`;
  elements.model.textContent = prediction.model;
}

function renderChart(points) {
  // Replace the chart with the latest historical points.
  elements.pointCount.textContent = `${points.length} points`;
  elements.emptyChart.hidden = points.length > 0;
  elements.chart.hidden = points.length === 0;
  if (state.chart) state.chart.destroy();
  if (!points.length) return;
  state.chart = new Chart(elements.chart, {
    type: "line",
    data: {
      labels: points.map((point) => new Date(point.timestamp).toLocaleDateString()),
      datasets: [{ label: "Close", data: points.map((point) => Number(point.close)), borderColor: "#147d79", backgroundColor: "rgba(20, 125, 121, .12)", fill: true, tension: .25, pointRadius: 2 }],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: (value) => `$${value}` } }, x: { grid: { display: false } } } },
  });
}

async function loadDashboard() {
  // Load quote, prediction, and chart data together.
  const symbol = elements.symbol.value;
  setLoading(true);
  clearError();
  try {
    const [quote, prediction, history] = await Promise.all([
      getJson(`/quote/${symbol}`),
      getJson(`/predict/${symbol}`),
      getJson(`/history/${symbol}`),
    ]);
    renderQuote(quote);
    renderPrediction(prediction);
    renderChart(history);
    elements.updated.textContent = `Updated ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
}

async function checkApi() {
  // Show whether the backend is reachable.
  try {
    await getJson("/health");
    elements.status.textContent = "API online";
    elements.statusDot.classList.add("online");
  } catch {
    elements.status.textContent = "API unavailable";
  }
}

async function runNotebookAnalysis() {
  const symbol = elements.symbol.value;
  elements.analysisSymbol.textContent = symbol;
  elements.analysisLoading.hidden = false;
  elements.analysisError.hidden = true;
  elements.notebookContainer.hidden = true;
  elements.runAnalysis.disabled = true;

  // Show elapsed time so the user knows work is in progress.
  let seconds = 0;
  const timer = setInterval(() => {
    seconds++;
    elements.analysisSymbol.textContent = `${symbol} (${seconds}s)`;
  }, 1000);

  // Hard 3-minute timeout — notebooks with errors can hang indefinitely.
  const controller = new AbortController();
  const hardTimeout = setTimeout(() => controller.abort(), 180_000);

  try {
    const response = await fetch(`${API_BASE}/analyze/${symbol}`, { signal: controller.signal });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || `Request failed (${response.status})`);

    if (!result.success) throw new Error(result.error || "Analysis failed");

    if (result.html) {
      elements.notebookContainer.innerHTML = result.html;
      elements.notebookContainer.hidden = false;
    }
  } catch (error) {
    const msg = error.name === "AbortError" ? "Analysis timed out after 3 minutes" : error.message;
    elements.analysisError.textContent = `Analysis failed: ${msg}`;
    elements.analysisError.hidden = false;
  } finally {
    clearInterval(timer);
    clearTimeout(hardTimeout);
    elements.analysisLoading.hidden = true;
    elements.runAnalysis.disabled = false;
  }
}

async function addNewSymbol() {
  const sym = elements.customSymbol.value.trim().toUpperCase();
  if (!sym) return;

  elements.addSymbol.disabled = true;
  elements.addSymbolStatus.textContent = `Fetching data for ${sym}...`;
  elements.addSymbolStatus.style.color = "var(--muted)";

  try {
    const result = await fetch(`${API_BASE}/setup/${sym}`, { method: "POST" });
    const data = await result.json();
    if (!result.ok) throw new Error(data.detail || `Request failed (${result.status})`);

    // Add to dropdown if not already present.
    if (![...elements.symbol.options].some((o) => o.value === sym)) {
      const option = document.createElement("option");
      option.value = sym;
      option.textContent = sym;
      elements.symbol.appendChild(option);
    }
    elements.symbol.value = sym;
    elements.customSymbol.value = "";
    elements.addSymbolStatus.textContent =
      `${sym} ready — ${data.observations} bars, model: ${data.best_model}, predicted close: ${formatPrice(data.predicted_price)}`;
    elements.addSymbolStatus.style.color = "var(--teal)";
    loadDashboard();
  } catch (err) {
    elements.addSymbolStatus.textContent = `Failed: ${err.message}`;
    elements.addSymbolStatus.style.color = "var(--coral)";
  } finally {
    elements.addSymbol.disabled = false;
  }
}

// Load the first symbol and wire up user actions.
elements.refresh.addEventListener("click", loadDashboard);
elements.symbol.addEventListener("change", loadDashboard);
elements.runAnalysis.addEventListener("click", runNotebookAnalysis);
elements.addSymbol.addEventListener("click", addNewSymbol);
elements.customSymbol.addEventListener("keydown", (e) => { if (e.key === "Enter") addNewSymbol(); });
checkApi();
loadDashboard();