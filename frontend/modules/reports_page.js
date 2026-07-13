// frontend\modules\reports_page.js
import { requireAuth, getCurrentUser } from './auth.js';
import { getDailyReport, getMonthlyReport, getYearlyReport } from '../services/api.js';

requireAuth();
const user = getCurrentUser();
const allowed = user && (user.role === 'admin' || user.role === 'manager');

const accessDenied = document.getElementById('access-denied');
const reportsContent = document.getElementById('reports-content');

if (!allowed) {
  accessDenied.style.display = '';
  reportsContent.style.display = 'none';
  throw new Error('Access denied'); // stop the rest of the module running
} else {
  reportsContent.style.display = '';
}

const tabButtons = document.querySelectorAll('.tab-btn');
const dailyPicker = document.getElementById('daily-picker');
const monthlyPicker = document.getElementById('monthly-picker');
const yearlyPicker = document.getElementById('yearly-picker');
const monthlyBreakdownSection = document.getElementById('monthly-breakdown-section');

let currentPeriod = 'daily';

function today() {
  return new Date().toISOString().slice(0, 10);
}

dailyPicker.value = today();
monthlyPicker.value = today().slice(0, 7);
yearlyPicker.value = new Date().getFullYear();

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    tabButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentPeriod = btn.dataset.period;

    dailyPicker.style.display = currentPeriod === 'daily' ? '' : 'none';
    monthlyPicker.style.display = currentPeriod === 'monthly' ? '' : 'none';
    yearlyPicker.style.display = currentPeriod === 'yearly' ? '' : 'none';
    monthlyBreakdownSection.style.display = currentPeriod === 'yearly' ? '' : 'none';

    loadReport();
  });
});

[dailyPicker, monthlyPicker, yearlyPicker].forEach(el => {
  el.addEventListener('change', loadReport);
});

function renderSummary(report) {
  document.getElementById('summary-total-sales').textContent = `₦${Number(report.total_sales).toLocaleString()}`;
  document.getElementById('summary-total-profit').textContent = `₦${Number(report.total_profit).toLocaleString()}`;
  document.getElementById('summary-transaction-count').textContent = report.transaction_count;

  const breakdown = report.payment_breakdown || {};
  document.getElementById('payment-breakdown-list').innerHTML = Object.entries(breakdown)
    .map(([method, amount]) => `<li>${method}: ₦${Number(amount).toLocaleString()}</li>`)
    .join('');
}

function renderTopItems(topItems = []) {
  document.getElementById('top-items-body').innerHTML = topItems.map(p => `
    <tr><td>${p.name}</td><td>${p.quantity_sold}</td><td>₦${Number(p.revenue).toLocaleString()}</td></tr>
  `).join('');
}

function renderEmployeePerformance(perf = []) {
  document.getElementById('employee-performance-body').innerHTML = perf.map(e => `
    <tr><td>${e.name}</td><td>${e.transaction_count}</td><td>₦${Number(e.total_sales).toLocaleString()}</td></tr>
  `).join('');
}

function renderMonthlyBreakdown(monthlyBreakdown = []) {
  document.getElementById('monthly-breakdown-body').innerHTML = monthlyBreakdown.map(m => `
    <tr><td>${m.month}</td><td>₦${Number(m.total_sales).toLocaleString()}</td><td>₦${Number(m.total_profit).toLocaleString()}</td><td>${m.transaction_count}</td></tr>
  `).join('');
}

async function loadReport() {
  try {
    let data;
    if (currentPeriod === 'daily') {
      data = await getDailyReport(dailyPicker.value);
    } else if (currentPeriod === 'monthly') {
      data = await getMonthlyReport(monthlyPicker.value);
    } else {
      data = await getYearlyReport(yearlyPicker.value);
    }

    const report = data.report;
    renderSummary(report);
    renderTopItems(report.top_items);
    renderEmployeePerformance(report.employee_performance);
    if (currentPeriod === 'yearly') renderMonthlyBreakdown(report.monthly_breakdown);
  } catch (err) {
    console.error('Failed to load report:', err);
  }
}

async function renderTrendChart() {
  const canvas = document.getElementById('trend-chart');
  const ctx = canvas.getContext('2d');
  const days = [...Array(7)].map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    return d.toISOString().slice(0, 10);
  });

  const results = await Promise.all(days.map(d => getDailyReport(d).catch(() => null)));
  const values = results.map(r => (r ? Number(r.report.total_sales) : 0));
  const max = Math.max(...values, 1);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const barWidth = canvas.width / days.length - 10;

  values.forEach((v, i) => {
    const barHeight = (v / max) * (canvas.height - 30);
    const x = i * (barWidth + 10) + 5;
    const y = canvas.height - barHeight - 20;
    ctx.fillStyle = '#FF7A00';
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.fillStyle = '#9AA0AA';
    ctx.font = '10px sans-serif';
    ctx.fillText(days[i].slice(5), x, canvas.height - 5);
  });
}

loadReport();
renderTrendChart();