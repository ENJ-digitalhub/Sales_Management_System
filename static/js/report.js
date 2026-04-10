const reportTabs = document.querySelectorAll(".tab-btn");
const reportTotal = document.getElementById("reportTotal");
const reportCount = document.getElementById("reportCount");
const reportChart = document.getElementById("reportChart");
const reportPie = document.getElementById("reportPie");
const reportPieLegend = document.getElementById("reportPieLegend");
const reportLeaderboard = document.getElementById("reportLeaderboard");
const reportSubtitle = document.getElementById("reportSubtitle");
const chartTitle = document.getElementById("chartTitle");
const chartCaption = document.getElementById("chartCaption");
const pieTitle = document.getElementById("pieTitle");
const pieCaption = document.getElementById("pieCaption");
const leaderboardTitle = document.getElementById("leaderboardTitle");
const leaderboardCaption = document.getElementById("leaderboardCaption");

const reportCopy = {
    sales: {
        subtitle: "Review daily sales movement, payment distribution, and your highest-selling items.",
        chartTitle: "Daily Sales",
        chartCaption: "Sales totals by day",
        pieTitle: "Sales Distribution",
        pieCaption: "Completed, paid, unpaid, and pending split",
        leaderboardTitle: "Sales Leaderboard",
        leaderboardCaption: "Top products by value",
    },
    purchase: {
        subtitle: "Track purchase flow, expense distribution, and the products drawing the most spend.",
        chartTitle: "Daily Purchases",
        chartCaption: "Purchase totals by day",
        pieTitle: "Purchase Distribution",
        pieCaption: "Purchase status breakdown",
        leaderboardTitle: "Purchase Leaderboard",
        leaderboardCaption: "Top purchased products by value",
    },
    activity: {
        subtitle: "Measure user activity, contribution distribution, and the most active team members.",
        chartTitle: "Activity Frequency",
        chartCaption: "Recorded activity by day",
        pieTitle: "Contribution Distribution",
        pieCaption: "Percentage of total activity completed by each person",
        leaderboardTitle: "Activity Leaderboard",
        leaderboardCaption: "Most active users",
    },
};

function formatNaira(value) {
    return `N${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function applyReportCopy(reportType) {
    const copy = reportCopy[reportType];
    if (!copy) return;

    if (reportSubtitle) reportSubtitle.textContent = copy.subtitle;
    if (chartTitle) chartTitle.textContent = copy.chartTitle;
    if (chartCaption) chartCaption.textContent = copy.chartCaption;
    if (pieTitle) pieTitle.textContent = copy.pieTitle;
    if (pieCaption) pieCaption.textContent = copy.pieCaption;
    if (leaderboardTitle) leaderboardTitle.textContent = copy.leaderboardTitle;
    if (leaderboardCaption) leaderboardCaption.textContent = copy.leaderboardCaption;
}

function renderBars(points) {
    if (!reportChart) return;
    if (!points?.length) {
        reportChart.innerHTML = "<p>No chart data available.</p>";
        return;
    }

    const max = Math.max(...points.map((item) => Number(item.value || 0)), 1);
    reportChart.innerHTML = points.map((item) => `
        <div class="bar-item">
            <span>${item.label}</span>
            <div class="bar-track"><div class="bar-fill" style="width:${(Number(item.value || 0) / max) * 100}%"></div></div>
            <strong>${Number(item.value || 0).toLocaleString()}</strong>
        </div>
    `).join("");
}

function renderPie(items) {
    if (!reportPie || !reportPieLegend) return;
    if (!items?.length) {
        reportPie.style.background = "transparent";
        reportPieLegend.innerHTML = "<p>No pie data available.</p>";
        return;
    }

    const total = items.reduce((sum, item) => sum + Number(item.value || 0), 0) || 1;
    const colors = ["#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#8b5cf6", "#0891b2"];
    let current = 0;
    const stops = items.map((item, index) => {
        const start = current;
        current += (Number(item.value || 0) / total) * 100;
        return `${colors[index % colors.length]} ${start}% ${current}%`;
    });
    reportPie.style.background = `conic-gradient(${stops.join(", ")})`;
    reportPieLegend.innerHTML = items.map((item, index) => `
        <div class="legend-item">
            <span class="legend-color" style="background:${colors[index % colors.length]}"></span>
            <span>${item.label}</span>
            <strong>${Number(item.value || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}%${typeof item.count === "number" ? ` (${item.count})` : ""}</strong>
        </div>
    `).join("");
}

function renderLeaderboard(items, reportType) {
    if (!reportLeaderboard) return;
    if (!items?.length) {
        reportLeaderboard.innerHTML = "<p>No leaderboard data available.</p>";
        return;
    }

    reportLeaderboard.innerHTML = items.map((item, index) => `
        <div class="leaderboard-item">
            <span class="leader-rank">${index + 1}</span>
            <span class="leader-label">${item.label}</span>
            <strong>${reportType === "activity" ? Number(item.value || 0).toLocaleString() + " events" : formatNaira(item.value)}</strong>
        </div>
    `).join("");
}

async function loadReport(reportType) {
    if (!reportTotal) return;

    applyReportCopy(reportType);
    reportTotal.textContent = "--";

    try {
        const response = await fetch(`/api/reports/${reportType}`);
        const data = await response.json();
        if (!response.ok) {
            renderBars([]);
            renderPie([]);
            renderLeaderboard([], reportType);
            return;
        }

        reportTotal.textContent = reportType === "activity"
            ? `${data.summary?.count || 0} events`
            : formatNaira(data.summary?.total || 0);
        if (reportCount) {
            reportCount.textContent = `${data.summary?.count || 0} record${data.summary?.count === 1 ? "" : "s"}`;
        }

        renderBars(data.chart || []);
        renderPie(data.pie || []);
        renderLeaderboard(data.leaderboard || [], reportType);
    } catch (error) {
        console.error(error);
        renderBars([]);
        renderPie([]);
        renderLeaderboard([], reportType);
    }
}

reportTabs.forEach((tab) => {
    tab.addEventListener("click", async () => {
        reportTabs.forEach((item) => item.classList.remove("active"));
        tab.classList.add("active");
        await loadReport(tab.dataset.report);
    });
});

if (reportTabs.length > 0) {
    const activeTab = document.querySelector(".tab-btn.active");
    if (activeTab) loadReport(activeTab.dataset.report);
}
