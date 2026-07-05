// frontend/modules/reports.js
import { getToken, BASE_URL } from "./auth.js";

async function _authedFetch(path) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  const data = await response.json();
  return { ok: response.ok, status: response.status, data };
}

export async function getDailyReport(date) {
  const query = date ? `?date=${date}` : "";
  return _authedFetch(`/reports/daily${query}`);
}

export async function getMonthlyReport(month) {
  const query = month ? `?month=${month}` : "";
  return _authedFetch(`/reports/monthly${query}`);
}

export async function getYearlyReport(year) {
  const query = year ? `?year=${year}` : "";
  return _authedFetch(`/reports/yearly${query}`);
}

export async function getEmployeeReport(userId, from, to) {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const query = params.toString() ? `?${params.toString()}` : "";
  return _authedFetch(`/reports/employee/${userId}${query}`);
}