import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ci_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function login(email, password) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const { data } = await api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  localStorage.setItem("ci_token", data.access_token);
  localStorage.setItem("ci_user", JSON.stringify(data.user));
  return data.user;
}

export function logout() {
  localStorage.removeItem("ci_token");
  localStorage.removeItem("ci_user");
}

export function getCurrentUser() {
  const raw = localStorage.getItem("ci_user");
  return raw ? JSON.parse(raw) : null;
}

export async function fetchDashboardStats() {
  const { data } = await api.get("/dashboard/stats");
  return data;
}

export async function fetchCases(params = {}) {
  const { data } = await api.get("/cases", { params });
  return data;
}

export async function fetchSimilarCases(caseId) {
  const { data } = await api.get(`/cases/${caseId}/similar`);
  return data;
}

export async function fetchNetworkGraph(params = {}) {
  const { data } = await api.get("/network/graph", { params });
  return data;
}

export async function fetchPredictions() {
  const { data } = await api.get("/dashboard/predictions");
  return data;
}

export async function createChatSession() {
  const { data } = await api.post("/chat/sessions");
  return data;
}

export async function listChatSessions() {
  const { data } = await api.get("/chat/sessions");
  return data;
}

export async function getChatMessages(sessionId) {
  const { data } = await api.get(`/chat/sessions/${sessionId}/messages`);
  return data;
}

export async function sendChatMessage(sessionId, content, language = "en") {
  const { data } = await api.post(`/chat/sessions/${sessionId}/messages`, { content, language });
  return data;
}

export async function downloadChatTranscript(sessionId, filenameHint) {
  const response = await api.get(`/export/chat/${sessionId}/report`, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `${filenameHint || sessionId}_transcript.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function fetchAuditLogs(params = {}) {
  const { data } = await api.get("/audit/logs", { params });
  return data;
}

export default api;
