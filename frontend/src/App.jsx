import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import Login from "./Login";

function Badge({ children, tone = "" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

function CRMPanel({ onClose }) {
  const [tab, setTab] = useState("customers");
  const [customers, setCustomers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [custForm, setCustForm] = useState({ name: "", email: "", tier: "standard" });
  const [orderForm, setOrderForm] = useState({ product: "", status: "delivered", total: "", ordered_at: "" });

  useEffect(() => {
    api.customers().then(setCustomers).catch(() => {});
    api.orders().then(setOrders).catch(() => {});
  }, []);

  const submitCustomer = async (e) => {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const c = await api.createCustomer(custForm);
      setCustomers([c]);
      setCustForm({ name: "", email: "", tier: "standard" });
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const submitOrder = async (e) => {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const o = await api.createOrder({ ...orderForm, total: parseFloat(orderForm.total) });
      setOrders((prev) => [...prev, o]);
      setOrderForm({ product: "", status: "delivered", total: "", ordered_at: "" });
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>CRM</h2>
          <button className="secondary" onClick={onClose}>✕ Close</button>
        </div>
        <div className="auth-tabs" style={{ marginBottom: 16 }}>
          <button className={tab === "customers" ? "active" : ""} onClick={() => setTab("customers")}>Customers</button>
          <button className={tab === "orders" ? "active" : ""} onClick={() => setTab("orders")}>Orders</button>
        </div>
        {error && <div className="error">{error}</div>}

        {tab === "customers" && (
          <>
            <form onSubmit={submitCustomer} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
              <input placeholder="Name" value={custForm.name} onChange={(e) => setCustForm({ ...custForm, name: e.target.value })} required />
              <input placeholder="Email" type="email" value={custForm.email} onChange={(e) => setCustForm({ ...custForm, email: e.target.value })} required />
              <select value={custForm.tier} onChange={(e) => setCustForm({ ...custForm, tier: e.target.value })}>
                <option value="standard">Standard</option>
                <option value="gold">Gold</option>
                <option value="platinum">Platinum</option>
              </select>
              <button type="submit" disabled={loading}>Save Profile</button>
            </form>
            <table className="crm-table">
              <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Tier</th></tr></thead>
              <tbody>
                {customers.length === 0 && <tr><td colSpan={4} className="muted" style={{ textAlign: "center" }}>No customers yet.</td></tr>}
                {customers.map((c) => (
                  <tr key={c.id}><td>{c.id}</td><td>{c.name}</td><td>{c.email}</td><td><Badge>{c.tier}</Badge></td></tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {tab === "orders" && (
          <>
            <form onSubmit={submitOrder} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
              <input placeholder="Product" value={orderForm.product} onChange={(e) => setOrderForm({ ...orderForm, product: e.target.value })} required />
              <select value={orderForm.status} onChange={(e) => setOrderForm({ ...orderForm, status: e.target.value })}>
                <option value="pending">Pending</option>
                <option value="shipped">Shipped</option>
                <option value="delivered">Delivered</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <input placeholder="Total (₹)" type="number" min="1" value={orderForm.total} onChange={(e) => setOrderForm({ ...orderForm, total: e.target.value })} required />
              <input type="datetime-local" value={orderForm.ordered_at} onChange={(e) => setOrderForm({ ...orderForm, ordered_at: e.target.value })} required />
              <button type="submit" disabled={loading}>Add Order</button>
            </form>
            <table className="crm-table">
              <thead><tr><th>ID</th><th>Customer</th><th>Product</th><th>Status</th><th>Total</th><th>Ordered At</th></tr></thead>
              <tbody>
                {orders.length === 0 && <tr><td colSpan={6} className="muted" style={{ textAlign: "center" }}>No orders yet.</td></tr>}
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td>{o.id}</td><td>{o.customer_id}</td><td>{o.product}</td>
                    <td><Badge>{o.status}</Badge></td>
                    <td>₹{o.total}</td>
                    <td>{new Date(o.ordered_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}

function NewTicketForm({ onCreated, onCancel }) {
  const [form, setForm] = useState({ subject: "", message: "", order_id: "" });
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.orders().then(setOrders).catch(() => {});
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const payload = {
        subject: form.subject,
        message: form.message,
      };
      const ticket = await api.createTicket(payload);
      onCreated(ticket);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>New Ticket</h2>
          <button className="secondary" onClick={onCancel}>✕ Cancel</button>
        </div>
        {error && <div className="error">{error}</div>}
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <input
            placeholder="Subject"
            value={form.subject}
            onChange={(e) => setForm({ ...form, subject: e.target.value })}
            required minLength={3}
          />
          <textarea
            placeholder="Describe the issue..."
            rows={5}
            value={form.message}
            onChange={(e) => setForm({ ...form, message: e.target.value })}
            required minLength={10}
            style={{ resize: "vertical" }}
          />
          <button type="submit" disabled={loading}>Submit Ticket</button>
        </form>
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("td_user");
    return stored ? JSON.parse(stored) : null;
  });

  const [tickets, setTickets] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [context, setContext] = useState(null);
  const [triage, setTriage] = useState(null);
  const [draft, setDraft] = useState(null);
  const [traces, setTraces] = useState([]);
  const [pendingActions, setPendingActions] = useState([]);
  const [evalReport, setEvalReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showCRM, setShowCRM] = useState(false);
  const [showNewTicket, setShowNewTicket] = useState(false);

  const selected = useMemo(() => tickets.find((t) => t.id === selectedId), [tickets, selectedId]);

  const loadTickets = async () => {
    const data = await api.tickets();
    setTickets(data);
    if (!selectedId && data.length) setSelectedId(data[0].id);
  };

  useEffect(() => {
    if (!user) return;
    loadTickets().catch((e) => setError(e.message));
  }, [user]);

  useEffect(() => {
    if (!selectedId || !user) return;
    Promise.all([api.context(selectedId), api.traces(selectedId)])
      .then(([ctx, tr]) => { setContext(ctx); setTraces(tr); })
      .catch((e) => setError(e.message));
    setTriage(null);
    setDraft(null);
  }, [selectedId]);

  const runTriage = async () => {
    setLoading(true); setError("");
    try {
      setTriage(await api.triage(selectedId));
      setTraces(await api.traces(selectedId));
      await loadTickets();
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const generateDraft = async () => {
    setLoading(true); setError("");
    try {
      setDraft(await api.draft(selectedId));
      setTraces(await api.traces(selectedId));
      setPendingActions(await api.pendingActions());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const runEval = async () => {
    setLoading(true); setError("");
    try { setEvalReport(await api.evaluate()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const approveAction = async (actionId) => {
    setLoading(true); setError("");
    try {
      await api.approve(actionId, `approve-${actionId}-${Date.now()}`);
      setPendingActions(await api.pendingActions());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const logout = () => {
    localStorage.removeItem("td_token");
    localStorage.removeItem("td_user");
    setUser(null);
    setTickets([]);
    setSelectedId(null);
  };

  if (!user) {
    return <Login onLogin={(data) => setUser({ username: data.username, role: data.role })} />;
  }

  return (
    <div className="app">
      {showCRM && <CRMPanel onClose={() => setShowCRM(false)} />}
      {showNewTicket && (
        <NewTicketForm
          onCreated={(ticket) => {
            setShowNewTicket(false);
            loadTickets().then(() => setSelectedId(ticket.id));
          }}
          onCancel={() => setShowNewTicket(false)}
        />
      )}

      <header className="topbar">
        <div>
          <div className="eyebrow">AI SUPPORT OPERATIONS</div>
          <h1>TrustDesk</h1>
          <p>Grounded support decisions with approval-gated actions.</p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <button className="secondary" onClick={() => setShowCRM(true)} disabled={loading}>CRM</button>
          <button className="secondary" onClick={runEval} disabled={loading}>Run Evaluation</button>
          <div style={{ display: "flex", alignItems: "center", gap: 10, background: "rgba(255,255,255,.1)", borderRadius: 12, padding: "8px 14px" }}>
            <div style={{ width: 34, height: 34, borderRadius: "50%", background: "rgba(255,255,255,.25)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 15 }}>
              {user.username[0].toUpperCase()}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <span style={{ fontSize: 13, fontWeight: 700, lineHeight: 1 }}>{user.username}</span>
              <Badge>{user.role}</Badge>
            </div>
            <button className="secondary" style={{ padding: "5px 10px", fontSize: 12, marginLeft: 4 }} onClick={logout}>Sign out</button>
          </div>
        </div>
      </header>

      <main className="layout">
        <aside className="sidebar panel">
          <div className="section-title">
            <span>Tickets</span>
            <span className="count">{tickets.length}</span>
          </div>
          <button onClick={() => setShowNewTicket(true)} style={{ width: "100%", marginBottom: 10, fontSize: 13 }}>+ New Ticket</button>
          {tickets.length === 0 && <p className="muted" style={{ fontSize: 13 }}>No tickets yet. Create one to get started.</p>}
          {tickets.map((ticket) => (
            <button
              key={ticket.id}
              className={`ticket-row ${ticket.id === selectedId ? "selected" : ""}`}
              onClick={() => setSelectedId(ticket.id)}
            >
              <div className="ticket-top">
                <strong>{ticket.id}</strong>
                {ticket.priority && <Badge tone={ticket.priority}>{ticket.priority}</Badge>}
              </div>
              <div className="ticket-subject">{ticket.subject}</div>
              <div className="muted">{new Date(ticket.created_at).toLocaleDateString()}</div>
            </button>
          ))}
        </aside>

        <section className="content">
          {error && <div className="error">{error}</div>}

          {!selected && (
            <div className="panel" style={{ textAlign: "center", padding: 40 }}>
              <p className="muted">Add customers and orders via <b>CRM</b>, then create a ticket to get started.</p>
            </div>
          )}

          {selected && (
            <>
              <div className="panel ticket-header">
                <div>
                  <div className="eyebrow">{selected.id}</div>
                  <h2>{selected.subject}</h2>
                  <p>{selected.message}</p>
                </div>
                <div className="actions">
                  <button onClick={runTriage} disabled={loading}>Run triage</button>
                  <button onClick={generateDraft} disabled={loading}>Generate cited draft</button>
                </div>
              </div>

              <div className="grid">
                <div className="panel">
                  <div className="section-title">Customer / Order context</div>
                  <div className="context">
                    <div><span>Customer</span><b>{context?.customer?.name || "—"}</b></div>
                    <div><span>Tier</span><b>{context?.customer?.tier || "—"}</b></div>
                    <div><span>Order</span><b>{context?.order?.id || "—"}</b></div>
                    <div><span>Status</span><b>{context?.order?.status || "—"}</b></div>
                    <div><span>Total</span><b>{context?.order ? `₹${context.order.total}` : "—"}</b></div>
                  </div>
                </div>

                <div className="panel">
                  <div className="section-title">AI triage</div>
                  {triage ? (
                    <>
                      <div className="badge-line">
                        <Badge>{triage.category}</Badge>
                        <Badge tone={triage.priority}>{triage.priority}</Badge>
                        {triage.escalation && <Badge tone="urgent">ESCALATE</Badge>}
                      </div>
                      <p className="muted">{triage.rationale}</p>
                    </>
                  ) : <p className="muted">Run triage to classify this ticket.</p>}
                </div>
              </div>

              <div className="grid main-grid">
                <div className="panel draft-panel">
                  <div className="section-title">Grounded draft reply</div>
                  {draft ? (
                    <>
                      <div className="draft">{draft.draft}</div>
                      <div className="section-title small-title">Citations</div>
                      {draft.citations.length ? draft.citations.map((c) => (
                        <div className="citation" key={c.id}>
                          <b>{c.id} · {c.title}</b>
                          <span>{c.excerpt}</span>
                        </div>
                      )) : <p className="muted">No policy evidence was sufficient.</p>}
                      <div className="guardrail">
                        Guardrail: <b>{draft.guardrail}</b>
                        {draft.escalated && <span> · Human escalation required</span>}
                      </div>
                    </>
                  ) : <p className="muted">Generate a draft to see policy citations and safety decisions.</p>}
                </div>

                <div className="panel">
                  <div className="section-title">Trace</div>
                  {traces.length ? traces.map((t) => (
                    <div className="trace" key={t.id}>
                      <div><b>{t.run_type}</b><Badge>{t.final_status}</Badge></div>
                      <div className="muted">Guardrail: {t.guardrail_result}</div>
                      <div className="muted">Docs: {t.retrieved_doc_ids.join(", ") || "none"}</div>
                    </div>
                  )) : <p className="muted">No runs yet.</p>}
                </div>
              </div>
            </>
          )}

          {pendingActions.length > 0 && (
            <div className="panel">
              <div className="section-title">Pending approvals</div>
              {pendingActions.map((a) => (
                <div className="approval-row" key={a.id}>
                  <div>
                    <b>{a.tool_name.replaceAll("_", " ")}</b>
                    <span className="muted" style={{ marginLeft: 8 }}>Ticket: {a.ticket_id}</span>
                  </div>
                  <button onClick={() => approveAction(a.id)} disabled={loading} style={{ padding: "6px 14px", fontSize: 12 }}>
                    Approve
                  </button>
                </div>
              ))}
            </div>
          )}

          {evalReport && (
            <div className="panel evaluation">
              <div className="section-title">Evaluation summary</div>
              <div className="metrics">
                {evalReport.metrics.map((m) => (
                  <div className="metric" key={m.metric}>
                    <span>{m.metric.replaceAll("_", " ")}</span>
                    <strong>{Math.round(m.value * 100)}%</strong>
                    <small>{m.details}</small>
                  </div>
                ))}
              </div>
              <p className="muted" style={{ marginTop: 8, fontSize: 12 }}>
                Evaluated {evalReport.overall.cases} standard test cases against policy knowledge base.
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
