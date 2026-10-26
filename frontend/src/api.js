import axios from "axios";

const api = axios.create({ baseURL: "/api" });

// ---- Login session (kept in the browser so a refresh doesn't log you out) ----
export function saveSession(session) {
  localStorage.setItem("session", JSON.stringify(session));
}

export function getSession() {
  try {
    return JSON.parse(localStorage.getItem("session"));
  } catch {
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem("session");
}

// Attach the token to every request
api.interceptors.request.use((config) => {
  const session = getSession();
  if (session) config.headers.Authorization = `Bearer ${session.token}`;
  return config;
});

// If the token has expired, send the user back to the login page
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const isLoginCall = err.config?.url?.startsWith("/auth/");
    if (err.response?.status === 401 && !isLoginCall) {
      clearSession();
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// Turn any API error into one readable sentence
export function errorMessage(err) {
  const detail = err.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg.replace("Value error, ", "")).join(" ");
  return "Something went wrong. Please try again.";
}

export default api;
