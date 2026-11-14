import React, { useEffect, useState } from "react";

type Tab =
  | "onboarding"
  | "inbox"
  | "studio"
  | "pipeline"
  | "messages"
  | "runs"
  | "analytics"
  | "settings";

export default function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("gigbid_token"));
  const [email, setEmail] = useState("reviewer@gigbid.ai");
  const [password, setPassword] = useState("gigbid2026");
  const [loginErr, setLoginErr] = useState("");

  const [tab, setTab] = useState<Tab>("inbox");
  const [jobs, setJobs] = useState<any[]>([]);
  const [portfolio, setPortfolio] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<any | null>(null);

  const [appState, setAppState] = useState<any>({ approvals: [], runs: [], messages: [], settings: {} });
  const [analytics, setAnalytics] = useState<any>({ ablation: [], kpis: {} });

  // Streaming Proposal Studio state
  const [streaming, setStreaming] = useState(false);
  const [liveSteps, setLiveSteps] = useState<any[]>([]);
  const [activeDraft, setActiveDraft] = useState<any | null>(null);
  const [editedLetter, setEditedLetter] = useState("");

  // New message form
  const [newClient, setNewClient] = useState("Nova AI Labs");
  const [newSubject, setNewSubject] = useState("RAG Evaluation & Guardrails");
  const [newIncoming, setNewIncoming] = useState("Can we schedule a quick call tomorrow to review your pgvector benchmarks?");

  const refreshData = async () => {
    const [jobsRes, stateRes, anaRes] = await Promise.all([
      fetch("/api/jobs").then((r) => r.json()),
      fetch("/api/state").then((r) => r.json()),
      fetch("/api/analytics").then((r) => r.json()),
    ]);
    setJobs(jobsRes.jobs || []);
    setPortfolio(jobsRes.portfolio || []);
    if (!selectedJob && jobsRes.jobs?.length) setSelectedJob(jobsRes.jobs[0]);
    setAppState(stateRes);
    setAnalytics(anaRes);
  };

  useEffect(() => {
    if (token) refreshData();
  }, [token]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginErr("");
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      setLoginErr("Invalid credentials. Use reviewer@gigbid.ai / gigbid2026");
      return;
    }
    const data = await res.json();
    localStorage.setItem("gigbid_token", data.token);
    setToken(data.token);
  };

  const runBidAgent = (job: any) => {
    setSelectedJob(job);
    setTab("studio");
    setStreaming(true);
    setLiveSteps([]);
    setActiveDraft(null);

    const es = new EventSource(`/api/stream-bid/${job.id}`);
    es.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.type === "node") {
        setLiveSteps((prev) => [...prev, msg.step]);
      } else if (msg.type === "complete") {
        setActiveDraft(msg.approval);
        setEditedLetter(msg.approval.cover_letter || "");
        setStreaming(false);
        es.close();
        refreshData();
      }
    };
    es.onerror = () => {
      setStreaming(false);
      es.close();
    };
  };

  const decideApproval = async (runId: string, approved: boolean, letter?: string) => {
    await fetch(`/api/approvals/${runId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved, edited_cover_letter: letter }),
    });
    if (activeDraft?.id === runId) {
      setActiveDraft({
        ...activeDraft,
        status: approved ? "APPROVED_AND_SUBMITTED" : "REJECTED_BY_HUMAN",
      });
    }
    refreshData();
  };

  const draftClientReply = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch("/api/messages/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client: newClient, job_title: newSubject, incoming: newIncoming }),
    });
    refreshData();
  };

  const approveMsg = async (id: string) => {
    await fetch(`/api/messages/${id}/approve`, { method: "POST" });
    refreshData();
  };

  if (!token) {
    return (
      <div className="login-wrap">
        <form className="card login-box" onSubmit={handleLogin}>
          <h2 style={{ marginTop: 0, color: "var(--accent)" }}>GigBid Reviewer Portal</h2>
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            Sign in to inspect LangGraph runs, streaming proposals, and persistent approvals.
          </p>
          <label>Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} />
          <div style={{ height: 12 }} />
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {loginErr && <p style={{ color: "var(--red)", fontSize: "0.85rem" }}>{loginErr}</p>}
          <button className="btn" style={{ width: "100%", marginTop: 16 }} type="submit">
            Sign In
          </button>
        </form>
      </div>
    );
  }

  const pendingCount = (appState.approvals || []).filter((a: any) => a.status === "PENDING_APPROVAL").length;

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">⚡ GigBid AI</div>
        {[
          ["onboarding", "1. Onboarding"],
          ["inbox", "2. Job Inbox"],
          ["studio", "3. Proposal Studio"],
          ["pipeline", "4. Pipeline"],
          ["messages", "5. Messages"],
          ["runs", "6. Agent Run Viewer"],
          ["analytics", "7. Analytics"],
          ["settings", "8. Settings"],
        ].map(([key, label]) => (
          <button
            key={key}
            className={`nav-btn ${tab === key ? "active" : ""}`}
            onClick={() => setTab(key as Tab)}
          >
            <span>{label}</span>
            {key === "pipeline" && pendingCount > 0 && <span className="badge amber">{pendingCount}</span>}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <button
          className="btn btn-outline"
          onClick={() => {
            localStorage.removeItem("gigbid_token");
            setToken(null);
          }}
        >
          Sign Out
        </button>
      </aside>

      <main className="main">
        {tab === "onboarding" && (
          <div>
            <h2>Freelancer Profile & Portfolio MCP</h2>
            <div className="card">
              <span className="badge green">MCP Server Connected</span>
              <h3>Verified Portfolio Evidence ({portfolio.length} items)</h3>
              <p style={{ color: "var(--muted)" }}>
                Indexed in pgvector with Outcome-Aware scoring and exposed via <code>gigbid-portfolio-mcp</code>.
              </p>
              {portfolio.map((p, idx) => (
                <div key={idx} className="card" style={{ background: "#0b0f19" }}>
                  <strong>{p.title || p.id}</strong> — <span className="badge">{p.type || "case_study"}</span>
                  <p style={{ color: "var(--muted)", marginBottom: 0 }}>{p.outcome || p.description || JSON.stringify(p)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "inbox" && (
          <div>
            <h2>Job Inbox & Opportunity Triage</h2>
            <div className="grid-2">
              <div>
                {jobs.map((j) => (
                  <div
                    key={j.id}
                    className="card"
                    style={{
                      cursor: "pointer",
                      borderColor: selectedJob?.id === j.id ? "var(--accent)" : "var(--border)",
                    }}
                    onClick={() => setSelectedJob(j)}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <strong>{j.title}</strong>
                      <span className="badge">${j.budget_min} - ${j.budget_max}</span>
                    </div>
                    <p style={{ color: "var(--muted)", fontSize: "0.88rem" }}>{j.description}</p>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {(j.skills || []).map((s: string) => (
                        <span key={s} className="badge">{s}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div>
                {selectedJob && (
                  <div className="card">
                    <span className="badge green">Selected Opportunity</span>
                    <h3>{selectedJob.title}</h3>
                    <p style={{ color: "var(--muted)" }}>{selectedJob.description}</p>
                    <p><strong>Client Budget:</strong> ${selectedJob.budget_min} – ${selectedJob.budget_max} USD</p>
                    <button className="btn" onClick={() => runBidAgent(selectedJob)}>
                      🚀 Run Multi-Agent Bid Graph
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {tab === "studio" && (
          <div>
            <h2>Proposal Studio (Live SSE LangGraph Stream)</h2>
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <strong>Target Job:</strong> {selectedJob?.title || "Select a job from Inbox"}
                </div>
                {selectedJob && (
                  <button className="btn" disabled={streaming} onClick={() => runBidAgent(selectedJob)}>
                    {streaming ? "Streaming Agent Nodes..." : "Re-Run Graph"}
                  </button>
                )}
              </div>

              <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
                {liveSteps.map((s, i) => (
                  <span key={i} className="badge green">✓ {s.node}</span>
                ))}
              </div>
            </div>

            {activeDraft && (
              <div className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h3>Human-in-the-Loop Approval Gate</h3>
                  <span className={`badge ${activeDraft.status === "PENDING_APPROVAL" ? "amber" : "green"}`}>
                    {activeDraft.status}
                  </span>
                </div>
                <p>
                  <strong>Decision:</strong> {activeDraft.decision} | <strong>Quote:</strong> $
                  {activeDraft.quote?.amount} | <strong>Fit Score:</strong> {activeDraft.fit_score} |{" "}
                  <strong>Compliance:</strong> {activeDraft.compliance?.passed ? "PASSED" : "BLOCKED"}
                </p>

                {activeDraft.status === "PENDING_APPROVAL" ? (
                  <>
                    <label>Editable Cover Letter (Claim-Verified)</label>
                    <textarea
                      rows={8}
                      value={editedLetter}
                      onChange={(e) => setEditedLetter(e.target.value)}
                    />
                    <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
                      <button
                        className="btn btn-green"
                        onClick={() => decideApproval(activeDraft.id, true, editedLetter)}
                      >
                        ✓ Approve & Submit Proposal
                      </button>
                      <button
                        className="btn btn-red"
                        onClick={() => decideApproval(activeDraft.id, false)}
                      >
                        ✕ Reject Draft
                      </button>
                    </div>
                  </>
                ) : (
                  <pre style={{ whiteSpace: "pre-wrap", color: "var(--muted)" }}>{activeDraft.cover_letter}</pre>
                )}
              </div>
            )}
          </div>
        )}

        {tab === "pipeline" && (
          <div>
            <h2>Proposal Pipeline & Persistent Approval Queue</h2>
            <p style={{ color: "var(--muted)" }}>
              All pending approvals are persisted server-side and survive full browser refreshes.
            </p>
            <div className="card">
              <table>
                <thead>
                  <tr>
                    <th>Run ID</th>
                    <th>Job</th>
                    <th>Quote</th>
                    <th>Fit</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(appState.approvals || []).map((a: any) => (
                    <tr key={a.id}>
                      <td><code>{a.id}</code></td>
                      <td>{a.job_title}</td>
                      <td>${a.quote?.amount}</td>
                      <td>{a.fit_score}</td>
                      <td>
                        <span className={`badge ${a.status === "PENDING_APPROVAL" ? "amber" : a.status.includes("APPROVED") ? "green" : "red"}`}>
                          {a.status}
                        </span>
                      </td>
                      <td>
                        {a.status === "PENDING_APPROVAL" ? (
                          <div style={{ display: "flex", gap: 6 }}>
                            <button className="btn btn-green" onClick={() => decideApproval(a.id, true)}>Approve</button>
                            <button className="btn btn-red" onClick={() => decideApproval(a.id, false)}>Reject</button>
                          </div>
                        ) : (
                          <span style={{ color: "var(--muted)" }}>Finalized</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === "messages" && (
          <div>
            <h2>Client Messages & Conversation Graph</h2>
            <form className="card" onSubmit={draftClientReply}>
              <h3>Simulate Incoming Client Message</h3>
              <div className="grid-2">
                <div>
                  <label>Client Name</label>
                  <input value={newClient} onChange={(e) => setNewClient(e.target.value)} />
                </div>
                <div>
                  <label>Job Context</label>
                  <input value={newSubject} onChange={(e) => setNewSubject(e.target.value)} />
                </div>
              </div>
              <label>Client Message</label>
              <textarea rows={2} value={newIncoming} onChange={(e) => setNewIncoming(e.target.value)} />
              <button className="btn" style={{ marginTop: 12 }} type="submit">
                Classify Intent & Draft Reply
              </button>
            </form>

            {(appState.messages || []).map((m: any) => (
              <div key={m.id} className="card">
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <strong>{m.client} — {m.job_title}</strong>
                  <span className="badge">{m.intent}</span>
                </div>
                <p style={{ color: "var(--muted)" }}><strong>Client:</strong> "{m.incoming}"</p>
                <p><strong>Agent Draft:</strong> {m.draft_reply}</p>
                {m.status === "PENDING_APPROVAL" ? (
                  <button className="btn btn-green" onClick={() => approveMsg(m.id)}>Approve & Send Reply</button>
                ) : (
                  <span className="badge green">✓ Sent</span>
                )}
              </div>
            ))}
          </div>
        )}

        {tab === "runs" && (
          <div>
            <h2>Agent Run Viewer (Execution Traces)</h2>
            {(appState.runs || []).length === 0 && (
              <div className="card">No runs recorded yet. Trigger a run from the Job Inbox!</div>
            )}
            {(appState.runs || []).map((r: any) => (
              <div key={r.run_id} className="card">
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <strong>{r.job_title} (<code>{r.run_id}</code>)</strong>
                  <span className="badge">{r.status}</span>
                </div>
                <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {(r.steps || []).map((s: any, idx: number) => (
                    <span key={idx} className="badge green">{idx + 1}. {s.node}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "analytics" && (
          <div>
            <h2>RAG & Multi-Agent Evaluation Analytics</h2>
            <div className="grid-4" style={{ marginBottom: 18 }}>
              <div className="card">
                <div style={{ color: "var(--muted)" }}>Jobs Evaluated</div>
                <h2>{analytics.kpis?.total_jobs_evaluated}</h2>
              </div>
              <div className="card">
                <div style={{ color: "var(--muted)" }}>Selective Bid Rate</div>
                <h2>{analytics.kpis?.bid_rate}</h2>
              </div>
              <div className="card">
                <div style={{ color: "var(--muted)" }}>Avg Graph Latency</div>
                <h2>{analytics.kpis?.avg_latency_sec}s</h2>
              </div>
              <div className="card">
                <div style={{ color: "var(--muted)" }}>Compliance Pass Rate</div>
                <h2 style={{ color: "var(--green)" }}>{analytics.kpis?.compliance_pass_rate}</h2>
              </div>
            </div>

            <div className="card">
              <h3>RAG Ablation Study Results</h3>
              <table>
                <thead>
                  <tr>
                    <th>Retrieval Variant</th>
                    <th>Recall@5</th>
                    <th>nDCG</th>
                    <th>Client Reply Rate</th>
                    <th>Hallucination Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {(analytics.ablation || []).map((row: any, idx: number) => (
                    <tr key={idx}>
                      <td><strong>{row.variant}</strong></td>
                      <td>{row.recall_at_5}</td>
                      <td>{row.ndcg}</td>
                      <td style={{ color: "var(--green)" }}>{(row.reply_rate * 100).toFixed(0)}%</td>
                      <td>{(row.hallucination_rate * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === "settings" && (
          <div>
            <h2>System & MCP Configuration</h2>
            <div className="card">
              <p><strong>Active RAG Pipeline:</strong> {appState.settings?.rag_variant}</p>
              <p><strong>Inference Model:</strong> {appState.settings?.model}</p>
              <p><strong>Max Critic Revision Loops:</strong> {appState.settings?.max_critic_revisions}</p>
              <p><strong>Portfolio MCP Command:</strong></p>
              <code style={{ display: "block", padding: 10, background: "#0b0f19", borderRadius: 8 }}>
                {appState.settings?.mcp_endpoint}
              </code>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}