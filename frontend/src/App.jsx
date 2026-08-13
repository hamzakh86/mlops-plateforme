import {
  Activity,
  BarChart3,
  Boxes,
  BrainCircuit,
  CheckCircle2,
  Database,
  FileSearch,
  Gauge,
  GitBranch,
  LayoutDashboard,
  Loader2,
  LogOut,
  RefreshCcw,
  Rocket,
  Search,
  Server,
  ShieldCheck,
  TriangleAlert,
  User,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import logoImg from "./assets/logo.png";

const links = [
  { label: "Swagger", href: "/docs" },
  { label: "Metrics", href: "/metrics" },
  { label: "MLflow", href: "http://127.0.0.1:5000" },
  { label: "Prometheus", href: "http://127.0.0.1:9090" },
  { label: "Grafana", href: "http://127.0.0.1:3001" },
];

const initialRevenue = {
  num_engineers: 45,
  active_projects: 16,
  avg_contract_value: 4800,
  lag_1: 72500,
  lag_2: 68000,
  lag_3: 65400,
};

const examples = {
  ask: "Quelles metriques sont utilisees pour superviser les endpoints IA ?",
  extract: "Facture ITGate Group du 10/08/2026. Montant total: 1250.50 TND.",
  classify: "Rapport technique de supervision Prometheus, Grafana et fallback LLM.",
  categories: "Facture, CV, Contrat, Rapport",
};

async function request(path, payload) {
  const token = localStorage.getItem("access_token");
  const headers = payload ? { "Content-Type": "application/json" } : {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(path, {
    method: payload ? "POST" : "GET",
    headers,
    body: payload ? JSON.stringify(payload) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || `Erreur HTTP ${response.status}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

function formatJson(value) {
  return JSON.stringify(value, null, 2);
}

function statusLabel(value) {
  return value ? "Operationnel" : "Indisponible";
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState("");
  const [activeSection, setActiveSection] = useState("dashboard");
  const [activityLog, setActivityLog] = useState([]);
  const [loading, setLoading] = useState("");
  const [results, setResults] = useState({});
  const [revenue, setRevenue] = useState(initialRevenue);
  const [askQuestion, setAskQuestion] = useState(examples.ask);
  const [extractText, setExtractText] = useState(examples.extract);
  const [classifyText, setClassifyText] = useState(examples.classify);
  const [categories, setCategories] = useState(examples.categories);
  const [token, setToken] = useState(() => localStorage.getItem("access_token"));
  const [loginError, setLoginError] = useState("");

  const isAuthenticated = Boolean(token);

  const healthCards = useMemo(() => [
    {
      label: "API",
      value: health?.status || (healthError ? "Erreur" : "Verification"),
      ok: !healthError,
      icon: Server,
    },
    {
      label: "Modele ML",
      value: statusLabel(health?.model_loaded),
      ok: health?.model_loaded,
      icon: BrainCircuit,
    },
    {
      label: "Moteur RAG",
      value: statusLabel(health?.rag_loaded),
      ok: health?.rag_loaded,
      icon: Database,
    },
    {
      label: "Score R2",
      value: health?.model_info?.r2 ?? "-",
      ok: true,
      icon: Gauge,
    },
  ], [health, healthError]);

  async function refreshHealth() {
    try {
      const data = await request("/health");
      setHealth(data);
      setHealthError("");
    } catch (error) {
      setHealthError(error.message);
    }
  }

  async function refreshHistory() {
    if (!token) return;
    try {
      const data = await request("/history");
      if (Array.isArray(data)) setActivityLog(data);
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
  }

  useEffect(() => {
    if (token) {
      refreshHealth();
      refreshHistory();
    }
    const interval = window.setInterval(() => {
      if (token) {
        refreshHealth();
        refreshHistory();
      }
    }, 30000);
    return () => window.clearInterval(interval);
  }, [token]);

  async function runAction(endpoint, action) {
    setLoading(endpoint);
    setResults((current) => ({ ...current, [endpoint]: { status: "En cours" } }));
    try {
      const data = await action();
      setResults((current) => ({ ...current, [endpoint]: data }));
      refreshHealth();
      refreshHistory();
    } catch (error) {
      const payload = { error: error.message };
      setResults((current) => ({ ...current, [endpoint]: payload }));
      refreshHistory();
    } finally {
      setLoading("");
    }
  }

  function predict(event) {
    event.preventDefault();
    runAction("/predict", () => request("/predict", { data: [revenue] }));
  }

  function ask(event) {
    event.preventDefault();
    runAction("/ask", () => request("/ask", { question: askQuestion }));
  }

  function extract(event) {
    event.preventDefault();
    runAction("/extract", () => request("/extract", { text: extractText }));
  }

  function classify(event) {
    event.preventDefault();
    const parsedCategories = categories.split(",").map((item) => item.trim()).filter(Boolean);
    runAction("/classify", () => request("/classify", {
      text: classifyText,
      categories: parsedCategories,
    }));
  }

  async function login(event) {
    event.preventDefault();
    setLoginError("");
    const formData = new FormData(event.target);
    try {
      const response = await fetch("/token", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Erreur de connexion");

      localStorage.setItem("access_token", data.access_token);
      setToken(data.access_token);
      refreshHealth();
    } catch (error) {
      setLoginError(error.message);
    }
  }

  function logout() {
    localStorage.removeItem("access_token");
    setToken(null);
  }

  if (!isAuthenticated) {
    return (
      <div className="login-shell">
        <div className="login-card">
          <div className="login-logo">
            <img src={logoImg} alt="ITGate Group Logo" />
            <div>
              <span>ITGate Group</span>
              <strong>MLOps Platform</strong>
            </div>
          </div>
          <div className="login-divider" />
          <form className="login-form" onSubmit={login}>
            <div className="login-field">
              <label className="login-field-label" htmlFor="username">Utilisateur</label>
              <input
                id="username"
                name="username"
                className="login-input"
                required
                defaultValue="admin"
                placeholder="Nom d'utilisateur"
                autoComplete="username"
              />
            </div>
            <div className="login-field">
              <label className="login-field-label" htmlFor="password">Mot de passe</label>
              <input
                id="password"
                type="password"
                name="password"
                className="login-input"
                required
                defaultValue="admin"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>
            {loginError && <div className="login-error">{loginError}</div>}
            <button className="login-btn" type="submit">Se connecter →</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" style={{ background: "transparent", border: "none" }}>
            <img src={logoImg} alt="ITGate Logo" style={{ width: "32px", height: "32px", objectFit: "contain" }} />
          </div>
          <div>
            <span>ITGate Group</span>
            <strong>MLOps Platform</strong>
          </div>
        </div>

        <nav className="nav-list" aria-label="Navigation principale">
          <button className={activeSection === "dashboard" ? "active" : ""} onClick={() => setActiveSection("dashboard")}>
            <LayoutDashboard size={18} /> Dashboard
          </button>
          <button className={activeSection === "ml" ? "active" : ""} onClick={() => setActiveSection("ml")}>
            <BrainCircuit size={18} /> Inference ML
          </button>
          <button className={activeSection === "documents" ? "active" : ""} onClick={() => setActiveSection("documents")}>
            <FileSearch size={18} /> IA documents
          </button>
          <button className={activeSection === "ops" ? "active" : ""} onClick={() => setActiveSection("ops")}>
            <Activity size={18} /> Observabilite
          </button>
          <button className={activeSection === "deploy" ? "active" : ""} onClick={() => setActiveSection("deploy")}>
            <Rocket size={18} /> Deploiement
          </button>
        </nav>
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar"><User size={16} /></div>
            <span>admin</span>
          </div>
          <button className="logout-btn" onClick={logout} title="Se déconnecter">
            <LogOut size={16} />
            Déconnexion
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Plateforme de pilotage</p>
            <h1>Supervision MLOps, inference et IA metier</h1>
          </div>
          <div className="top-actions">
            {links.map((link) => (
              <a key={link.label} href={link.href} target="_blank" rel="noreferrer">{link.label}</a>
            ))}
            <button className="icon-btn" onClick={refreshHealth} title="Rafraichir la sante">
              <RefreshCcw size={18} />
            </button>
          </div>
        </header>

        <section className="status-grid">
          {healthCards.map((card) => {
            const Icon = card.icon;
            return (
              <article className="status-card" key={card.label}>
                <div className="card-icon"><Icon size={20} /></div>
                <span>{card.label}</span>
                <strong className={card.ok ? "ok" : "warn"}>{card.value}</strong>
              </article>
            );
          })}
        </section>

        {activeSection === "dashboard" && (
          <Dashboard health={health} healthError={healthError} activityLog={activityLog} setActiveSection={setActiveSection} />
        )}

        {activeSection === "ml" && (
          <section className="content-grid">
            <Panel title="Prevision CA ITGate (Multi-varie)" eyebrow="Serie Temporelle & IA Metier" icon={BrainCircuit}>
              <form className="iris-grid" onSubmit={predict}>
                <label>
                  Ingenieurs ITGate
                  <input
                    type="number"
                    value={revenue.num_engineers}
                    onChange={(e) => setRevenue({ ...revenue, num_engineers: Number(e.target.value) })}
                  />
                </label>
                <label>
                  Projets En Cours
                  <input
                    type="number"
                    value={revenue.active_projects}
                    onChange={(e) => setRevenue({ ...revenue, active_projects: Number(e.target.value) })}
                  />
                </label>
                <label>
                  Valeur Contrat Moy. (TND)
                  <input
                    type="number"
                    value={revenue.avg_contract_value}
                    onChange={(e) => setRevenue({ ...revenue, avg_contract_value: Number(e.target.value) })}
                  />
                </label>
                <label>
                  Revenu M-1 (TND)
                  <input
                    type="number"
                    value={revenue.lag_1}
                    onChange={(e) => setRevenue({ ...revenue, lag_1: Number(e.target.value) })}
                  />
                </label>
                <label>
                  Revenu M-2 (TND)
                  <input
                    type="number"
                    value={revenue.lag_2}
                    onChange={(e) => setRevenue({ ...revenue, lag_2: Number(e.target.value) })}
                  />
                </label>
                <label>
                  Revenu M-3 (TND)
                  <input
                    type="number"
                    value={revenue.lag_3}
                    onChange={(e) => setRevenue({ ...revenue, lag_3: Number(e.target.value) })}
                  />
                </label>
                <button className="primary-btn" disabled={loading === "/predict"} style={{ gridColumn: "span 2" }}>
                  {loading === "/predict" ? <Loader2 className="spin" size={17} /> : <Search size={17} />}
                  Predire le CA du Mois M+1
                </button>
              </form>
              <ResultBlock value={results["/predict"]} />
            </Panel>

            <Panel title="Graphique & Data Drift" eyebrow="Supervision en Temps Reel" icon={BarChart3}>
              <div style={{ padding: "10px 0" }}>
                <p style={{ fontSize: "0.85rem", color: "var(--muted)", margin: "0 0 12px" }}>
                  <strong>Courbe Historique & Prédiction Futurs (ITGate Group)</strong>
                </p>
                <svg viewBox="0 0 400 150" style={{ width: "100%", height: "140px", background: "rgba(15,23,42,0.6)", borderRadius: "8px", padding: "10px" }}>
                  {/* Grid Lines */}
                  <line x1="10" y1="120" x2="390" y2="120" stroke="rgba(255,255,255,0.1)" />
                  <line x1="10" y1="80" x2="390" y2="80" stroke="rgba(255,255,255,0.1)" />
                  <line x1="10" y1="40" x2="390" y2="40" stroke="rgba(255,255,255,0.1)" />
                  
                  {/* Historical Curve */}
                  <polyline
                    fill="none"
                    stroke="#0f766e"
                    strokeWidth="3"
                    points="20,110 70,95 120,105 170,75 220,60 270,68 320,40"
                  />
                  {/* Historical Points */}
                  <circle cx="20" cy="110" r="4" fill="#0f766e" />
                  <circle cx="70" cy="95" r="4" fill="#0f766e" />
                  <circle cx="120" cy="105" r="4" fill="#0f766e" />
                  <circle cx="170" cy="75" r="4" fill="#0f766e" />
                  <circle cx="220" cy="60" r="4" fill="#0f766e" />
                  <circle cx="270" cy="68" r="4" fill="#0f766e" />
                  <circle cx="320" cy="40" r="4" fill="#0f766e" />

                  {/* Forecast Line (Dashed Green) */}
                  <line x1="320" y1="40" x2="380" y2="22" stroke="#22c55e" strokeWidth="3" strokeDasharray="5,5" />
                  <circle cx="380" cy="22" r="5" fill="#22c55e" />

                  <text x="325" y="140" fill="#cbd5df" fontSize="10">2026 Q3</text>
                  <text x="370" y="140" fill="#22c55e" fontSize="10" fontWeight="bold">M+1</text>
                </svg>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "14px", padding: "10px", background: "var(--surface-soft)", borderRadius: "8px", border: "1px solid var(--line)" }}>
                  <div>
                    <span style={{ fontSize: "0.78rem", color: "var(--muted)", display: "block" }}>Statut Data Drift</span>
                    <strong style={{ color: "#22c55e", fontSize: "0.95rem" }}>🟢 AUCUNE DÉRIVE (NORMAL)</strong>
                  </div>
                  <span className="badge">Z-score: 0.42</span>
                </div>
              </div>
            </Panel>
          </section>
        )}

        {activeSection === "documents" && (
          <section className="content-grid">
            <TextTool title="Question RAG" eyebrow="Recherche documentaire" icon={FileSearch} value={askQuestion} setValue={setAskQuestion} onSubmit={ask} loading={loading === "/ask"} result={results["/ask"]} button="Interroger" />
            <TextTool title="Extraction" eyebrow="Informations structurees" icon={Search} value={extractText} setValue={setExtractText} onSubmit={extract} loading={loading === "/extract"} result={results["/extract"]} button="Extraire" />
            <Panel title="Classification" eyebrow="Zero-shot" icon={ShieldCheck}>
              <form className="stack-form" onSubmit={classify}>
                <textarea rows={5} value={classifyText} onChange={(event) => setClassifyText(event.target.value)} />
                <input value={categories} onChange={(event) => setCategories(event.target.value)} />
                <button className="primary-btn" disabled={loading === "/classify"}>
                  {loading === "/classify" ? <Loader2 className="spin" size={17} /> : <ShieldCheck size={17} />}
                  Classifier
                </button>
              </form>
              <ResultBlock value={results["/classify"]} />
            </Panel>
          </section>
        )}

        {activeSection === "ops" && <Observability activityLog={activityLog} />}
        {activeSection === "deploy" && <Deployment />}
      </main>
    </div>
  );
}

function Dashboard({ health, healthError, activityLog, setActiveSection }) {
  return (
    <section className="dashboard-grid">
      <article className="hero-panel">
        <p className="eyebrow">Vue operationnelle</p>
        <h2>Une console unique pour tester, observer et presenter la plateforme.</h2>
        <div className="hero-actions">
          <button onClick={() => setActiveSection("ml")}><BrainCircuit size={17} /> Tester le modele</button>
          <button onClick={() => setActiveSection("documents")}><FileSearch size={17} /> Tester le RAG</button>
        </div>
      </article>
      <ActivityPanel activityLog={activityLog} />
      <article className="panel compact">
        <div className="panel-title">
          <TriangleAlert size={20} />
          <div>
            <p className="eyebrow">Etat detaille</p>
            <h2>Runtime</h2>
          </div>
        </div>
        <ResultBlock value={healthError ? { error: healthError } : health} />
      </article>
    </section>
  );
}

function Observability({ activityLog }) {
  return (
    <section className="content-grid">
      <Panel title="Observabilite" eyebrow="Prometheus + Grafana" icon={BarChart3}>
        <div className="ops-grid">
          <MetricTile label="Endpoint metrics" value="/metrics" />
          <MetricTile label="Grafana" value=":3001" />
          <MetricTile label="Prometheus" value=":9090" />
          <MetricTile label="Fallback LLM" value="trace" />
        </div>
      </Panel>
      <ActivityPanel activityLog={activityLog} />
    </section>
  );
}

function Deployment() {
  const steps = [
    ["Docker", "Image multi-stage avec utilisateur non-root et frontend React inclus."],
    ["Kubernetes", "Deployment, Service, ConfigMap, Secret Groq et HPA."],
    ["CI/CD", "Tests, build Docker, tags SHA court et publication GHCR."],
    ["Monitoring", "Annotations Prometheus et dashboard Grafana provisionne."],
  ];

  return (
    <section className="content-grid">
      <Panel title="Deploiement" eyebrow="Docker, Kubernetes, GHCR" icon={Rocket}>
        <div className="timeline">
          {steps.map(([title, text]) => (
            <div className="timeline-row" key={title}>
              <CheckCircle2 size={20} />
              <div>
                <strong>{title}</strong>
                <span>{text}</span>
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Commandes utiles" eyebrow="Demo Windows" icon={GitBranch}>
        <pre className="command-block">{`python src/train.py
uvicorn src.serve:app --host 127.0.0.1 --port 8000 --reload
npm --prefix frontend run dev
docker compose -f docker-compose.monitoring.yml up --build -d
.\\scripts\\docker_smoke_test.ps1 -ImageTag smoke`}</pre>
      </Panel>
    </section>
  );
}

function Panel({ title, eyebrow, icon: Icon, children }) {
  return (
    <article className="panel">
      <div className="panel-title">
        <Icon size={20} />
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
      </div>
      {children}
    </article>
  );
}

function TextTool({ title, eyebrow, icon, value, setValue, onSubmit, loading, result, button }) {
  const Icon = icon;
  return (
    <Panel title={title} eyebrow={eyebrow} icon={Icon}>
      <form className="stack-form" onSubmit={onSubmit}>
        <textarea rows={5} value={value} onChange={(event) => setValue(event.target.value)} />
        <button className="primary-btn" disabled={loading}>
          {loading ? <Loader2 className="spin" size={17} /> : <Icon size={17} />}
          {button}
        </button>
      </form>
      <ResultBlock value={result} />
    </Panel>
  );
}

function ResultBlock({ value }) {
  return <pre className="result-block">{value ? formatJson(value) : "Aucun resultat pour le moment."}</pre>;
}

function ActivityPanel({ activityLog }) {
  return (
    <article className="panel compact">
      <div className="panel-title">
        <Activity size={20} />
        <div>
          <p className="eyebrow">Pilotage</p>
          <h2>Activite recente</h2>
        </div>
      </div>
      <div className="activity-list">
        {activityLog.length === 0 && <span className="empty">Aucun appel lance depuis l'interface.</span>}
        {activityLog.map((item, index) => (
          <div className="activity-row" key={`${item.endpoint}-${item.at}-${index}`}>
            <strong>{item.endpoint}</strong>
            <span>{item.at} - {item.detail}</span>
            <em className={item.error ? "badge error" : item.status === "Fallback" ? "badge fallback" : "badge"}>{item.status}</em>
          </div>
        ))}
      </div>
    </article>
  );
}

function PipelineCard({ health }) {
  return (
    <Panel title="Pipeline MLflow" eyebrow="Tracking" icon={GitBranch}>
      <div className="pipeline">
        <div><span>Experience</span><strong>{health?.model_info?.experiment || "Iris_Classification"}</strong></div>
        <div><span>Run actif</span><strong>{health?.model_info?.run_id || "-"}</strong></div>
        <div><span>RAG run</span><strong>{health?.rag_info?.run_id || "-"}</strong></div>
      </div>
    </Panel>
  );
}

function MetricTile({ label, value }) {
  return (
    <div className="metric-tile">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
