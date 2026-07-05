// frontend/modules/reports_page.js
import { getCurrentUser, requireAuth } from "./auth.js";
import { getDailyReport, getMonthlyReport, getYearlyReport } from "./reports.js";

requireAuth();

const currentUser = getCurrentUser();
const isAuthorized = currentUser && (currentUser.role === "admin" || currentUser.role === "manager");

// Role check happens immediately, before any report content is built or
// fetched — an employee hitting this URL directly never sees the page
// shell, the tabs, or triggers a single API call. This is the answer to
// "what happens if an employee navigates here directly": nothing renders,
// full stop, checked at the very top of page logic, not after a fetch
// resolves (which would briefly flash real content first).
if (!isAuthorized) {
  document.getElementById("access-denied").style.display = "block";
} else {
  document.getElementById("reports-content").style.display = "block";
  initReportsPage();
}

function initReportsPage() {
  let currentPeriod = "daily";

  const dailyPicker = document.getElementById("daily-picker");
  const monthlyPicker = document.getElementById("monthly-picker");
  const yearlyPicker = document.getElementById("yearly-picker");

  const today = new Date();
  dailyPicker.value = today.toISOString().slice(0, 10);
  monthlyPicker.value = today.toISOString().slice(0, 7);
  yearlyPicker.value = today.getFullYear();

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentPeriod = btn.dataset.period;

      dailyPicker.style.display = currentPeriod === "daily" ? "" : "none";
      monthlyPicker.style.display = currentPeriod === "monthly" ? "" : "none";
      yearlyPicker.style.display = currentPeriod === "yearly" ? "" : "none";

      document.getElementById("top-products-section").style.display =
        currentPeriod === "yearly" ? "none" : "";
      document.getElementById("employee-performance-section").style.display =
        currentPeriod === "yearly" ? "none" : "";
      document.getElementById("monthly-breakdown-section").style.display =
        currentPeriod === "yearly" ? "" : "none";

      loadReport();
    });
  });

  dailyPicker.addEventListener("change", loadReport);
  monthlyPicker.addEventListener("change", loadReport);
  yearlyPicker.addEventListener("change", loadReport);

  async function loadReport() {
    let result;

    if (currentPeriod === "daily") {
      result = await getDailyReport(dailyPicker.value);
    } else if (currentPeriod === "monthly") {
      result = await getMonthlyReport(monthlyPicker.value);
    } else {
      result = await getYearlyReport(yearlyPicker.value);
    }

    if (!result.ok) {
      alert(result.data.message || "Failed to load report");
      return;
    }

    renderReport(result.data.report, currentPeriod);
  }

  function renderReport(report, period) {
    document.getElementById("summary-total-sales").textContent = report.total_sales.toFixed(2);
    document.getElementById("summary-total-profit").textContent = report.total_profit.toFixed(2);
    document.getElementById("summary-transaction-count").textContent = report.transaction_count;

    const breakdownList = document.getElementById("payment-breakdown-list");
    breakdownList.innerHTML = "";
    for (const [method, amount] of Object.entries(report.payment_breakdown || {})) {
      const li = document.createElement("li");
      li.textContent = `${method}: ${amount.toFixed(2)}`;
      breakdownList.appendChild(li);
    }

    if (period !== "yearly") {
      const topProductsBody = document.getElementById("top-products-body");
      topProductsBody.innerHTML = "";
      for (const p of report.top_products || []) {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${p.name}</td><td>${p.quantity_sold}</td><td>${p.revenue.toFixed(2)}</td>`;
        topProductsBody.appendChild(row);
      }

      const empBody = document.getElementById("employee-performance-body");
      empBody.innerHTML = "";
      for (const e of report.employee_performance || []) {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${e.name}</td><td>${e.transaction_count}</td><td>${e.total_sales.toFixed(2)}</td>`;
        empBody.appendChild(row);
      }
    } else {
      const monthlyBody = document.getElementById("monthly-breakdown-body");
      monthlyBody.innerHTML = "";
      for (const m of report.monthly_breakdown || []) {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${m.month}</td><td>${m.total_sales.toFixed(2)}</td><td>${m.total_profit.toFixed(2)}</td><td>${m.transaction_count}</td>`;
        monthlyBody.appendChild(row);
      }
    }
  }

  async function loadTrendChart() {
    // Fire all 7 requests concurrently with Promise.all rather than
    // awaiting them one at a time in a loop — sequential awaits would
    // take 7x as long since each fetch would wait for the previous one.
    const dates = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      dates.push(d.toISOString().slice(0, 10));
    }

    const results = await Promise.all(dates.map((date) => getDailyReport(date)));

    const points = results.map((r, i) => ({
      date: dates[i],
      total: r.ok ? r.data.report.total_sales : 0,
    }));

    drawBarChart(points);
  }

  function drawBarChart(points) {
    const canvas = document.getElementById("trend-chart");
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const maxValue = Math.max(...points.map((p) => p.total), 1);
    const barWidth = canvas.width / points.length;
    const chartHeight = canvas.height - 40;

    points.forEach((point, i) => {
      const barHeight = (point.total / maxValue) * chartHeight;
      const x = i * barWidth + 10;
      const y = canvas.height - barHeight - 20;

      ctx.fillStyle = "#2c3e50";
      ctx.fillRect(x, y, barWidth - 20, barHeight);

      ctx.fillStyle = "#333";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(point.date.slice(5), x + (barWidth - 20) / 2, canvas.height - 5);
      ctx.fillText(point.total.toFixed(0), x + (barWidth - 20) / 2, y - 4);
    });
  }

  loadReport();
  loadTrendChart();
}