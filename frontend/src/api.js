const request = async (url, options = {}) => {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
};

export const api = {
  tickets: () => request("/api/tickets"),
  ticket: (id) => request(`/api/tickets/${id}`),
  context: (id) => request(`/api/tickets/${id}/context`),
  triage: (id) => request(`/api/tickets/${id}/triage`, { method: "POST" }),
  draft: (id) => request(`/api/tickets/${id}/draft`, { method: "POST" }),
  traces: (id) => request(`/api/tickets/${id}/trace`),
  evaluate: () => request("/api/evaluations/run", { method: "POST" }),
  approve: (id, key) =>
    request(`/api/actions/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ idempotency_key: key }),
    }),
};
