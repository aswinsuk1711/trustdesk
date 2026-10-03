const request = async (url, options = {}) => {
  const token = localStorage.getItem("td_token");
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });
  if (res.status === 401) {
    localStorage.removeItem("td_token");
    localStorage.removeItem("td_user");
    window.location.reload();
    return;
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
};

export const api = {
  login: (username, password) =>
    fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    }).then(async (res) => {
      if (!res.ok) throw new Error("Invalid username or password");
      return res.json();
    }),
  signup: (username, email, password) =>
    fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Signup failed");
      return data;
    }),
  verifyOtp: (email, otp) =>
    fetch("/api/auth/verify-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp }),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Invalid OTP");
      return data;
    }),
  resendOtp: (email) =>
    fetch("/api/auth/resend-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp: "" }),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to resend");
      return data;
    }),
  tickets: () => request("/api/tickets"),
  createTicket: (data) => request("/api/tickets", { method: "POST", body: JSON.stringify(data) }),
  ticket: (id) => request(`/api/tickets/${id}`),
  context: (id) => request(`/api/tickets/${id}/context`),
  triage: (id) => request(`/api/tickets/${id}/triage`, { method: "POST" }),
  draft: (id) => request(`/api/tickets/${id}/draft`, { method: "POST" }),
  traces: (id) => request(`/api/tickets/${id}/trace`),
  pendingActions: () => request("/api/actions/pending"),
  evaluate: () => request("/api/evaluations/run", { method: "POST" }),
  approve: (id, key) =>
    request(`/api/actions/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ idempotency_key: key }),
    }),
  customers: () => request("/api/crm/customers"),
  createCustomer: (data) => request("/api/crm/customers", { method: "POST", body: JSON.stringify(data) }),
  orders: () => request("/api/crm/orders"),
  createOrder: (data) => request("/api/crm/orders", { method: "POST", body: JSON.stringify(data) }),
};
