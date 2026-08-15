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

// Load the first symbol and wire up user actions.
elements.refresh.addEventListener("click", loadDashboard);
elements.symbol.addEventListener("change", loadDashboard);
checkApi();
loadDashboard();