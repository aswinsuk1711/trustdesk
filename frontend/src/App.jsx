import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

function Badge({ children, tone = "" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

function App() {
  const [tickets, setTickets] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [context, setContext] = useState(null);
  const [triage, setTriage] = useState(null);
  const [draft, setDraft] = useState(null);
  const [traces, setTraces] = useState([]);
  const [evalReport, setEvalReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selected = useMemo(
    () => tickets.find((t) => t.id === selectedId),
    [tickets, selectedId]
  );

  const loadTickets = async () => {
    const data = await api.tickets();
    setTickets(data);
    if (!selectedId && data.length) setSelectedId(data[0].id);
  };

  useEffect(() => { loadTickets().catch((e) => setError(e.message)); }, []);

  useEffect(() => {
    if (!selectedId) return;
    Promise.all([api.context(selectedId), api.traces(selectedId)])
      .then(([ctx, tr]) => { setContext(ctx); setTraces(tr); })
      .catch((e) => setError(e.message));
    setTriage(null);
    setDraft(null);
  }, [selectedId]);

  const runTriage = async () => {
    setLoading(true); setError("");
    try {
      const result = await api.triage(selectedId);
      setTriage(result);
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
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const runEval = async () => {
    setLoading(true); setError("");
    try { setEvalReport(await api.evaluate()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="eyebrow">AI SUPPORT OPERATIONS</div>
          <h1>TrustDesk</h1>
          <p>Grounded support decisions with approval-gated actions.</p>
        </div>
        <button className="secondary" onClick={runEval} disabled={loading}>Run evaluation</button>
      </header>

      <main className="layout">
        <aside className="sidebar panel">
          <div className="section-title">
            <span>Tickets</span><span className="count">{tickets.length}</span>
          </div>
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
              <div className="muted">{ticket.customer_id}</div>
            </button>
          ))}
        </aside>

        <section className="content">
          {error && <div className="error">{error}</div>}
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
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
