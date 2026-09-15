const API = "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("user_token");
  return token ? { Authorization: "Bearer " + token } : {};
}

async function request(path, options = {}) {
  const { method = "GET", body, formData = false } = options;
  const headers = { ...authHeaders() };
  let payload;
  if (body !== undefined) {
    if (formData) {
      payload = body;
    } else {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
  }
  const res = await fetch(API + path, { method, headers, body: payload });
  if (res.status === 401) {
    localStorage.removeItem("user_token");
    localStorage.removeItem("user_modules");
    localStorage.removeItem("user_email");
    window.location.href = "/login.html";
    throw new Error("Sesión vencida");
  }
  if (!res.ok) {
    let detail = "Error " + res.status;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch (e) {
      /* noop */
    }
    throw new Error(detail);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body }),
  put: (path, body) => request(path, { method: "PUT", body }),
  del: (path) => request(path, { method: "DELETE" }),
  upload: (path, file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request(path, { method: "POST", body: fd, formData: true });
  },
};

export function getSession() {
  return {
    token: localStorage.getItem("user_token"),
    modules: JSON.parse(localStorage.getItem("user_modules") || "[]"),
    email: localStorage.getItem("user_email") || "",
  };
}

export function logout() {
  localStorage.removeItem("user_token");
  localStorage.removeItem("user_modules");
  localStorage.removeItem("user_email");
  window.location.href = "/login.html";
}
