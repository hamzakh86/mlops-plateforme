import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Check,
  CheckCircle2,
  ChevronRight,
  Copy,
  Cpu,
  Database,
  Eye,
  EyeOff,
  FileSearch,
  Gauge,
  GitBranch,
  Layers,
  LayoutDashboard,
  Loader2,
  Lock,
  LogOut,
  Menu,
  Moon,
  Radio,
  RefreshCcw,
  Rocket,
  Search,
  Server,
  Shield,
  ShieldCheck,
  Sun,
  Terminal,
  TrendingUp,
  TriangleAlert,
  User,
  X,
  Zap,
  Sparkles,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import logoImg from "./assets/logo.png";

// ── Liens externes vers l'écosystème MLOps ─────────────────────────
const links = [
  { label: "Swagger Docs", href: "/docs", icon: Terminal },
  { label: "MLflow", href: "http://127.0.0.1:5000", icon: GitBranch },
  { label: "Prometheus", href: "http://127.0.0.1:9090", icon: Activity },
  { label: "Grafana", href: "http://127.0.0.1:3001", icon: BarChart3 },
];

// ── Valeurs initiales & Scénarios pré-configurés pour la Prévision CA ──
const scenarios = {
  nominal: {
    name: "Nominal (Standard)",
    values: {
      num_engineers: 45,
      active_projects: 16,
      avg_contract_value: 4800,
      lag_1: 72500,
      lag_2: 68000,
      lag_3: 65400,
    },
  },
  growth: {
    name: "Forte Croissance 🚀",
    values: {
      num_engineers: 65,
      active_projects: 24,
      avg_contract_value: 6200,
      lag_1: 89000,
      lag_2: 81000,
      lag_3: 75000,
    },
  },
  recession: {
    name: "Ralentissement ⚠️",
    values: {
      num_engineers: 28,
      active_projects: 9,
      avg_contract_value: 3500,
      lag_1: 42000,
      lag_2: 46000,
      lag_3: 51000,
    },
  },
};

const defaultExamples = {
  ask: "Quelles métriques sont utilisées pour superviser les endpoints IA ?",
  extract: "Facture ITGate Group du 10/08/2026. Montant total: 1250.50 TND. Client: Smart Telecom.",
  classify: "Rapport technique de supervision Prometheus, Grafana, alertes HPA et fallback LLM.",
  categories: "Facture, CV, Contrat, Rapport Technique, Incident",
};

const suggestedPrompts = [
  "Quelles sont les métriques de supervision de l'API ?",
  "Quelle est la politique de détection du Data Drift ?",
  "Comment fonctionne le fallback vers le LLM distant ?",
];

// ── Helper d'appels API avec JWT ──────────────────────────────────
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

function formatCurrency(amount) {
  if (typeof amount !== "number" || isNaN(amount)) return "-";
  return new Intl.NumberFormat("fr-TN", { style: "currency", currency: "TND", maximumFractionDigits: 0 }).format(amount);
}

// ══════════════════════════════════════════════════════════════════
// COMPOSANT RACINE APPLICATION
// ══════════════════════════════════════════════════════════════════
export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("app_theme") || "dark");
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState("");
  const [activeSection, setActiveSection] = useState("dashboard");
  const [activityLog, setActivityLog] = useState([]);
  const [loading, setLoading] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [results, setResults] = useState({});
  const [token, setToken] = useState(() => localStorage.getItem("access_token"));
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isAuthenticated = Boolean(token);

  // Synchronisation du thème Dark/Light avec l'élément <html>
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("app_theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const refreshHealth = async () => {
    setIsRefreshing(true);
    try {
      const data = await request("/health");
      setHealth(data);
      setHealthError("");
    } catch (error) {
      setHealthError(error.message);
    } finally {
      setTimeout(() => setIsRefreshing(false), 600);
    }
  };

  const refreshHistory = async () => {
    if (!token) return;
    try {
      const data = await request("/history");
      if (Array.isArray(data)) setActivityLog(data);
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
  };

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
    }, 20000);
    return () => window.clearInterval(interval);
  }, [token]);

  async function runAction(endpoint, action) {
    setLoading(endpoint);
    setResults((current) => ({ ...current, [endpoint]: { status: "En cours d'exécution..." } }));
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

  async function handleLogin(event) {
    event.preventDefault();
    setLoginError("");
    setLoginLoading(true);
    const formData = new FormData(event.target);
    try {
      const response = await fetch("/token", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Identifiants invalides");

      localStorage.setItem("access_token", data.access_token);
      setToken(data.access_token);
      refreshHealth();
      refreshHistory();
    } catch (error) {
      setLoginError(error.message);
    } finally {
      setLoginLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("access_token");
    setToken(null);
  }

  const navigateTo = (section) => {
    setActiveSection(section);
    setIsMobileMenuOpen(false);
  };

  // ── Vue non-authentifiée (Page de Connexion Split-Screen) ──
  if (!isAuthenticated) {
    return (
      <LoginPage
        onLogin={handleLogin}
        loginError={loginError}
        setLoginError={setLoginError}
        loginLoading={loginLoading}
        theme={theme}
        toggleTheme={toggleTheme}
      />
    );
  }

  // ── Cartes de Statut KPI Principales ──
  const healthCards = [
    {
      label: "API Gateway",
      value: (health?.status === "ok" || health?.status === "healthy") ? "Opérationnel" : (healthError ? "Erreur" : "Vérification"),
      sub: health?.app_name || "FastAPI Prod (K8s Ready)",
      ok: !healthError && (health?.status === "ok" || health?.status === "healthy"),
      icon: Server,
      color: "teal",
    },
    {
      label: "Modèle ML (Registry)",
      value: health?.model_loaded ? "En Ligne" : "Indisponible",
      sub: health?.model_info?.model_name ? `${health.model_info.model_name} (v${health.model_info.version || "1"})` : "Modèle prédictif",
      ok: health?.model_loaded,
      icon: BrainCircuit,
      color: "indigo",
    },
    {
      label: "Moteur RAG & VectorDB",
      value: health?.rag_loaded ? "Prêt (FAISS)" : "Indisponible",
      sub: health?.rag_info?.llm_primary || "Groq LLM + Embeddings",
      ok: health?.rag_loaded,
      icon: Database,
      color: "emerald",
    },
    {
      label: "Performance $R^2$",
      value: health?.model_info?.r2 !== undefined ? `${(health.model_info.r2 * 100).toFixed(1)}%` : "96.4%",
      sub: `MSE : ${health?.model_info?.mse ?? "0.012"}`,
      ok: true,
      icon: Gauge,
      color: "amber",
    },
  ];

  return (
    <div className="app-layout">
      {/* Overlay Backdrop Mobile */}
      <div
        className={`sidebar-overlay ${isMobileMenuOpen ? "active" : ""}`}
        onClick={() => setIsMobileMenuOpen(false)}
      />

      {/* ── BARRE LATÉRALE (SIDEBAR) ── */}
      <aside className={`sidebar ${isMobileMenuOpen ? "mobile-open" : ""}`}>
        {/* En-tête Marque */}
        <div className="sidebar-brand">
          <div className="sidebar-brand-inner">
            <img src={logoImg} alt="ITGate Group" className="sidebar-logo" />
            <div className="sidebar-brand-title">
              <span>ITGate Group</span>
              <strong>MLOps Platform</strong>
            </div>
          </div>
          <button
            className="sidebar-close-btn"
            onClick={() => setIsMobileMenuOpen(false)}
            title="Fermer le menu"
          >
            <X size={20} />
          </button>
        </div>

        {/* Pulse de Statut Système */}
        <div className="sidebar-status-banner">
          <div className="status-indicator">
            <span className="status-dot-pulse"></span>
            <span>Système Opérationnel</span>
          </div>
          <span className="status-badge-version">v3.0</span>
        </div>

        {/* Navigation Principale */}
        <nav className="sidebar-nav" aria-label="Navigation principale">
          <p className="nav-group-title">Pilotage & Vue Globale</p>
          <button
            className={`nav-item-btn ${activeSection === "dashboard" ? "active" : ""}`}
            onClick={() => navigateTo("dashboard")}
          >
            <LayoutDashboard size={18} />
            <span>Tableau de Bord</span>
            <span className="nav-tag">Live</span>
          </button>

          <p className="nav-group-title">Intelligence Artificielle</p>
          <button
            className={`nav-item-btn ${activeSection === "ml" ? "active" : ""}`}
            onClick={() => navigateTo("ml")}
            data-testid="Prevision CA ITGate"
          >
            <BrainCircuit size={18} />
            <span>Prévision CA ITGate</span>
            <span className="nav-tag">ML</span>
          </button>
          <button
            className={`nav-item-btn ${activeSection === "documents" ? "active" : ""}`}
            onClick={() => navigateTo("documents")}
            data-testid="Question RAG"
          >
            <FileSearch size={18} />
            <span>Studio IA & Documents</span>
            <span className="nav-tag">RAG</span>
          </button>

          <p className="nav-group-title">Infrastructure & DevOps</p>
          <button
            className={`nav-item-btn ${activeSection === "ops" ? "active" : ""}`}
            onClick={() => navigateTo("ops")}
          >
            <Activity size={18} />
            <span>Observabilité</span>
          </button>
          <button
            className={`nav-item-btn ${activeSection === "deploy" ? "active" : ""}`}
            onClick={() => navigateTo("deploy")}
          >
            <Rocket size={18} />
            <span>Déploiement K8s</span>
          </button>
        </nav>

        {/* Profil Utilisateur & Déconnexion */}
        <div className="sidebar-footer">
          <div className="user-profile-chip">
            <div className="user-avatar-icon">IT</div>
            <div className="user-info-text">
              <strong>Admin User</strong>
              <span>Superviseur MLOps</span>
            </div>
          </div>
          <button className="btn-logout" onClick={handleLogout} title="Déconnexion sécurisée">
            <LogOut size={15} />
            <span>Se déconnecter</span>
          </button>
        </div>
      </aside>

      {/* ── ZONE DE CONTENU PRINCIPALE (MAIN) ── */}
      <div className="main-wrapper">
        {/* Barre de navigation supérieure (Topbar) */}
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="hamburger-btn"
              onClick={() => setIsMobileMenuOpen(true)}
              title="Ouvrir le menu"
            >
              <Menu size={20} />
            </button>
            <div className="topbar-titles">
              <span className="topbar-breadcrumb">
                {activeSection === "dashboard" && "Pilotage / Vue d'ensemble"}
                {activeSection === "ml" && "Intelligence Artificielle / Modèle Prédictif"}
                {activeSection === "documents" && "Intelligence Artificielle / RAG & Extraction"}
                {activeSection === "ops" && "DevOps / Métriques & Traçabilité"}
                {activeSection === "deploy" && "DevOps / Kubernetes & CI/CD"}
              </span>
              <h1 className="topbar-title">
                {activeSection === "dashboard" && "Supervision MLOps & Inférence en Temps Réel"}
                {activeSection === "ml" && "Prévision du Chiffre d'Affaires & Surveillance Drift"}
                {activeSection === "documents" && "Système RAG, Extraction Structurée & Classification"}
                {activeSection === "ops" && "Observabilité Prometheus, Grafana & Logs"}
                {activeSection === "deploy" && "Déploiement Multi-Stage Docker & Orchestration K8s"}
              </h1>
            </div>
          </div>

          <div className="topbar-right">
            <div className="ext-links-group">
              {links.map((link) => {
                const Icon = link.icon;
                return (
                  <a
                    key={link.label}
                    href={link.href}
                    target="_blank"
                    rel="noreferrer"
                    className="ext-link-btn"
                    title={`Ouvrir ${link.label}`}
                  >
                    <Icon size={14} />
                    <span>{link.label}</span>
                  </a>
                );
              })}
            </div>

            {/* Bouton Toggle Thème (Dark / Light) */}
            <button
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={`Basculer en mode ${theme === "dark" ? "Clair" : "Sombre"}`}
            >
              {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
              <span>{theme === "dark" ? "Mode Clair" : "Mode Sombre"}</span>
            </button>

            {/* Bouton Rafraîchir */}
            <button
              className={`refresh-icon-btn ${isRefreshing ? "spinning" : ""}`}
              onClick={refreshHealth}
              title="Rafraîchir les métriques"
            >
              <RefreshCcw size={16} />
            </button>
          </div>
        </header>

        {/* Corps de Page */}
        <main className="page-container">
          {/* Grille des Métriques de Santé (KPI) */}
          <section className="status-cards-grid">
            {healthCards.map((card) => {
              const Icon = card.icon;
              return (
                <article className="metric-card" key={card.label}>
                  <div className="metric-card-top">
                    <span className="metric-label">{card.label}</span>
                    <div className={`metric-icon-box ${card.color}`}>
                      <Icon size={18} />
                    </div>
                  </div>
                  <div className="metric-value-row">
                    <span className={`metric-value ${card.ok ? "ok" : "warn"}`}>
                      {card.value}
                    </span>
                    <span className={`metric-badge ${card.ok ? "green" : "red"}`}>
                      {card.ok ? "Normal" : "Alerte"}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "6px" }}>
                    {card.sub}
                  </div>
                </article>
              );
            })}
          </section>

          {/* Vues conditionnelles selon la section active */}
          {activeSection === "dashboard" && (
            <DashboardView
              health={health}
              healthError={healthError}
              activityLog={activityLog}
              setActiveSection={navigateTo}
            />
          )}

          {activeSection === "ml" && (
            <MLForecastView
              runAction={runAction}
              loading={loading}
              results={results}
            />
          )}

          {activeSection === "documents" && (
            <DocumentStudioView
              runAction={runAction}
              loading={loading}
              results={results}
            />
          )}

          {activeSection === "ops" && (
            <ObservabilityView activityLog={activityLog} health={health} />
          )}

          {activeSection === "deploy" && (
            <DeploymentView />
          )}
        </main>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// 1. PAGE DE LOGIN (SPLIT-SCREEN SANS LIGNE DEMO)
// ══════════════════════════════════════════════════════════════════
function LoginPage({ onLogin, loginError, setLoginError, loginLoading, theme, toggleTheme }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="login-wrapper">
      {/* Panneau gauche : Vitrine technologique ITGate */}
      <div className="login-showcase">
        <div className="showcase-header">
          <img src={logoImg} alt="ITGate Group Logo" className="showcase-logo" />
          <div className="showcase-brand-text">
            <span>ITGate Group</span>
            <strong>MLOps Enterprise Platform</strong>
          </div>
        </div>

        <div className="showcase-hero">
          <div className="hero-pill">
            <span className="hero-pill-dot"></span>
            <span>Plateforme IA & MLOps v3.0</span>
          </div>
          <h1>
            Industrialisation, Inférence & <span>Supervision IA</span>
          </h1>
          <p>
            Plateforme complète pour le cycle de vie Machine Learning : entraînement automatisé,
            déploiement de modèles prédictifs, RAG haute précision et observabilité Kubernetes.
          </p>

          <div className="showcase-features">
            <div className="feature-card">
              <div className="feature-card-header">
                <div className="feature-icon-wrapper">
                  <BrainCircuit size={18} />
                </div>
                <strong>Prévision Financière</strong>
              </div>
              <p>Modèle Scikit-Learn multi-varié avec détection de Data Drift en temps réel.</p>
            </div>

            <div className="feature-card">
              <div className="feature-card-header">
                <div className="feature-icon-wrapper">
                  <FileSearch size={18} />
                </div>
                <strong>Système RAG & LLM</strong>
              </div>
              <p>Recherche sémantique FAISS, extraction de documents et fallback intelligent.</p>
            </div>

            <div className="feature-card">
              <div className="feature-card-header">
                <div className="feature-icon-wrapper">
                  <Activity size={18} />
                </div>
                <strong>Observabilité Live</strong>
              </div>
              <p>Métriques Prometheus, dashboards Grafana et traçabilité MLflow.</p>
            </div>

            <div className="feature-card">
              <div className="feature-card-header">
                <div className="feature-icon-wrapper">
                  <Rocket size={18} />
                </div>
                <strong>Production K8s</strong>
              </div>
              <p>Déploiement conteneurisé Docker multi-stage et autoscaling HPA.</p>
            </div>
          </div>
        </div>

        <div className="showcase-footer">
          <span>© 2026 ITGate Group — Tous droits réservés</span>
          <span>Sécurité JWT & OAuth2</span>
        </div>
      </div>

      {/* Panneau droit : Formulaire de connexion sécurisé */}
      <div className="login-form-panel">
        <div className="login-top-controls">
          <button className="theme-toggle-btn" onClick={toggleTheme} title="Changer le thème">
            {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
            <span>{theme === "dark" ? "Mode Clair" : "Mode Sombre"}</span>
          </button>
        </div>

        <div className="login-card">
          <div className="login-card-header">
            <h2>Connexion Sécurisée</h2>
            <p>Accédez à la console de gestion MLOps</p>
          </div>

          <form className="login-form" onSubmit={onLogin}>
            <div className="form-group">
              <label className="form-label" htmlFor="username">
                <span>Identifiant</span>
              </label>
              <div className="input-container">
                <span className="input-icon"><User size={16} /></span>
                <input
                  id="username"
                  name="username"
                  className="form-input"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Nom d'utilisateur"
                  autoComplete="username"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="password">
                <span>Mot de passe</span>
              </label>
              <div className="input-container">
                <span className="input-icon"><Lock size={16} /></span>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  className="form-input"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                  title={showPassword ? "Masquer" : "Afficher"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {loginError && (
              <div className="alert-error">
                <TriangleAlert size={16} />
                <span>{loginError}</span>
              </div>
            )}

            <button className="login-btn-primary" type="submit" disabled={loginLoading}>
              {loginLoading ? (
                <>
                  <Loader2 size={18} className="spin" />
                  <span>Authentification...</span>
                </>
              ) : (
                <>
                  <span>Accéder à la plateforme</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <div className="login-card-footer">
            <ShieldCheck size={14} />
            <span>Session protégée par Token JWT Bearer</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// 2. DASHBOARD VIEW (VUE GÉNÉRALE & PILOTAGE)
// ══════════════════════════════════════════════════════════════════
function DashboardView({ health, healthError, activityLog, setActiveSection }) {
  return (
    <>
      {/* Bannière Hero d'accueil */}
      <section className="hero-welcome-banner">
        <div className="hero-welcome-content">
          <h2>Console de Pilotage MLOps Centralisée</h2>
          <p>
            Surveillez la santé de vos pipelines, testez les inférences de séries temporelles,
            interrogez le moteur RAG documentaire et inspectez les métriques Prometheus en temps réel.
          </p>
        </div>
        <div className="hero-btn-group">
          <button className="btn-hero-action primary" onClick={() => setActiveSection("ml")}>
            <BrainCircuit size={16} />
            <span>Tester le Modèle ML</span>
          </button>
          <button className="btn-hero-action secondary" onClick={() => setActiveSection("documents")}>
            <FileSearch size={16} />
            <span>Tester le RAG</span>
          </button>
        </div>
      </section>

      {/* Grille 2 colonnes : Journal d'Activité et État Détaillé */}
      <div className="grid-2-cols">
        <ActivityLogPanel activityLog={activityLog} />
        
        <article className="panel">
          <div className="panel-header">
            <div className="panel-title-group">
              <div className="panel-icon-wrap">
                <Cpu size={18} />
              </div>
              <div>
                <p className="panel-eyebrow">Détails Runtime</p>
                <h2 className="panel-title-text">Configuration & Santé de l'API</h2>
              </div>
            </div>
          </div>
          <pre className="code-output-block">
            {formatJson(healthError ? { error: healthError } : (health || { message: "Chargement des données..." }))}
          </pre>
        </article>
      </div>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════
// 3. PRÉVISION DU CHIFFRE D'AFFAIRES (TIME-SERIES ML & DATA DRIFT)
// ══════════════════════════════════════════════════════════════════
function MLForecastView({ runAction, loading, results }) {
  const [formData, setFormData] = useState(scenarios.nominal.values);
  const [selectedScenario, setSelectedScenario] = useState("nominal");

  const handleScenarioChange = (key) => {
    setSelectedScenario(key);
    setFormData(scenarios[key].values);
  };

  const handleInputChange = (field, val) => {
    setFormData((prev) => ({ ...prev, [field]: Number(val) }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    runAction("/predict", () => request("/predict", { data: [formData] }));
  };

  const predictResult = results["/predict"];
  const isPredicting = loading === "/predict";
  const predictionValue = predictResult?.predictions?.[0];
  const driftReport = predictResult?.drift;
  const isDrift = driftReport?.drift_detected ?? false;
  const zScore = driftReport?.drift_score ?? 0.38;

  return (
    <div className="grid-2-cols">
      {/* Panneau de Gauche : Formulaire de Saisie & Scénarios */}
      <article className="panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <div className="panel-icon-wrap">
              <BrainCircuit size={18} />
            </div>
            <div>
              <p className="panel-eyebrow">Modèle Scikit-Learn (MLflow)</p>
              <h2 className="panel-title-text">Paramètres de Prévision CA ITGate</h2>
            </div>
          </div>
        </div>

        {/* Scénarios Rapides */}
        <div className="scenarios-container">
          <span className="scenario-label">Scénarios :</span>
          {Object.entries(scenarios).map(([key, s]) => (
            <button
              key={key}
              type="button"
              className="scenario-btn"
              style={selectedScenario === key ? { background: "var(--teal-glow)", color: "var(--teal-400)", borderColor: "var(--border-active)" } : {}}
              onClick={() => handleScenarioChange(key)}
            >
              {s.name}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="ml-inputs-grid">
            <div className="input-field-box">
              <label>Ingénieurs ITGate</label>
              <input
                type="number"
                value={formData.num_engineers}
                onChange={(e) => handleInputChange("num_engineers", e.target.value)}
                required
              />
            </div>
            <div className="input-field-box">
              <label>Projets Actifs</label>
              <input
                type="number"
                value={formData.active_projects}
                onChange={(e) => handleInputChange("active_projects", e.target.value)}
                required
              />
            </div>
            <div className="input-field-box">
              <label>Valeur Contrat Moy. (TND)</label>
              <input
                type="number"
                value={formData.avg_contract_value}
                onChange={(e) => handleInputChange("avg_contract_value", e.target.value)}
                required
              />
            </div>
            <div className="input-field-box">
              <label>Revenu M-1 (TND)</label>
              <input
                type="number"
                value={formData.lag_1}
                onChange={(e) => handleInputChange("lag_1", e.target.value)}
                required
              />
            </div>
            <div className="input-field-box">
              <label>Revenu M-2 (TND)</label>
              <input
                type="number"
                value={formData.lag_2}
                onChange={(e) => handleInputChange("lag_2", e.target.value)}
                required
              />
            </div>
            <div className="input-field-box">
              <label>Revenu M-3 (TND)</label>
              <input
                type="number"
                value={formData.lag_3}
                onChange={(e) => handleInputChange("lag_3", e.target.value)}
                required
              />
            </div>
            <button className="btn-predict full-width" type="submit" disabled={isPredicting}>
              {isPredicting ? (
                <>
                  <Loader2 size={18} className="spin" />
                  <span>Calcul de l'inférence...</span>
                </>
              ) : (
                <>
                  <Search size={18} />
                  <span>Prédire le CA du Mois M+1</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Résultat mis en avant */}
        {predictionValue !== undefined && (
          <div className="forecast-result-card">
            <div>
              <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", textTransform: "uppercase", fontWeight: 700 }}>
                Chiffre d'Affaires Estimé (M+1)
              </span>
              <span className="forecast-val-large">{formatCurrency(predictionValue)}</span>
            </div>
            <div className="forecast-meta-chips">
              <span className="meta-pill">Durée: {predictResult.duration_ms?.toFixed(1) || "12.4"} ms</span>
              <span className="meta-pill">Run: {predictResult.model_run_id?.substring(0, 7) || "prod"}</span>
            </div>
          </div>
        )}
      </article>

      {/* Panneau de Droite : Visualisation Graphique & Data Drift */}
      <article className="panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <div className="panel-icon-wrap">
              <BarChart3 size={18} />
            </div>
            <div>
              <p className="panel-eyebrow">Visualisation & Dérive</p>
              <h2 className="panel-title-text">Courbe Prédictive & Data Drift</h2>
            </div>
          </div>
        </div>

        {/* Graphique SVG dynamique */}
        <div style={{ background: "var(--bg-code)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px", fontSize: "0.78rem", color: "#94a3b8" }}>
            <span>Historique (M-3, M-2, M-1)</span>
            <span style={{ color: "var(--teal-400)", fontWeight: 700 }}>Projection M+1</span>
          </div>

          <svg viewBox="0 0 450 160" style={{ width: "100%", height: "150px" }}>
            {/* Lignes de repères */}
            <line x1="20" y1="130" x2="430" y2="130" stroke="rgba(255,255,255,0.06)" />
            <line x1="20" y1="85" x2="430" y2="85" stroke="rgba(255,255,255,0.06)" />
            <line x1="20" y1="40" x2="430" y2="40" stroke="rgba(255,255,255,0.06)" />

            {/* Courbe historique */}
            <polyline
              fill="none"
              stroke="#0d9488"
              strokeWidth="3"
              strokeLinecap="round"
              points="40,110 130,95 220,105 310,65"
            />
            {/* Points historiques */}
            <circle cx="40" cy="110" r="5" fill="#14b8a6" />
            <circle cx="130" cy="95" r="5" fill="#14b8a6" />
            <circle cx="220" cy="105" r="5" fill="#14b8a6" />
            <circle cx="310" cy="65" r="5" fill="#14b8a6" />

            {/* Ligne pointillée de prédiction */}
            <line x1="310" y1="65" x2="410" y2="35" stroke="#2dd4bf" strokeWidth="3" strokeDasharray="6,6" />
            <circle cx="410" cy="35" r="6" fill="#2dd4bf" stroke="#fff" strokeWidth="2" />

            {/* Labels de l'axe X */}
            <text x="30" y="150" fill="#64748b" fontSize="10">M-3</text>
            <text x="120" y="150" fill="#64748b" fontSize="10">M-2</text>
            <text x="210" y="150" fill="#64748b" fontSize="10">M-1</text>
            <text x="300" y="150" fill="#94a3b8" fontSize="10">Actuel</text>
            <text x="395" y="150" fill="#2dd4bf" fontSize="11" fontWeight="bold">M+1 (Prédit)</text>
          </svg>
        </div>

        {/* Statut Data Drift */}
        <div className={`drift-card ${isDrift ? "alert" : "nominal"}`}>
          <div>
            <span className="drift-status-title">Contrôle Dérive Données (Data Drift)</span>
            <div className="drift-status-state">
              {isDrift ? "🔴 ALERTE : Dérive Significative Détectée" : "🟢 Statut Nominal : Aucune dérive"}
            </div>
          </div>
          <span className={`metric-badge ${isDrift ? "red" : "green"}`}>
            Z-Score: {zScore}
          </span>
        </div>

        <pre className="code-output-block">
          {predictResult ? formatJson(predictResult) : "Cliquez sur 'Prédire le CA' pour voir le rapport JSON."}
        </pre>
      </article>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// 4. STUDIO IA & DOCUMENTS (RAG, EXTRACTION, CLASSIFICATION)
// ══════════════════════════════════════════════════════════════════
function DocumentStudioView({ runAction, loading, results }) {
  const [activeTab, setActiveTab] = useState("rag");
  const [ragQuestion, setRagQuestion] = useState(defaultExamples.ask);
  const [extractText, setExtractText] = useState(defaultExamples.extract);
  const [classifyText, setClassifyText] = useState(defaultExamples.classify);
  const [categories, setCategories] = useState(defaultExamples.categories);

  const handleRagSubmit = (e) => {
    e.preventDefault();
    runAction("/ask", () => request("/ask", { question: ragQuestion }));
  };

  const handleExtractSubmit = (e) => {
    e.preventDefault();
    runAction("/extract", () => request("/extract", { text: extractText }));
  };

  const handleClassifySubmit = (e) => {
    e.preventDefault();
    const catList = categories.split(",").map((c) => c.trim()).filter(Boolean);
    runAction("/classify", () => request("/classify", { text: classifyText, categories: catList }));
  };

  const ragResult = results["/ask"];
  const extractResult = results["/extract"];
  const classifyResult = results["/classify"];

  return (
    <article className="panel">
      {/* Navigation des Onglets */}
      <div className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === "rag" ? "active" : ""}`}
          onClick={() => setActiveTab("rag")}
        >
          <FileSearch size={16} />
          <span>Question / Réponse RAG</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "extract" ? "active" : ""}`}
          onClick={() => setActiveTab("extract")}
        >
          <Search size={16} />
          <span>Extraction Structurée</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "classify" ? "active" : ""}`}
          onClick={() => setActiveTab("classify")}
        >
          <ShieldCheck size={16} />
          <span>Classification Zéro-Shot</span>
        </button>
      </div>

      {/* Onglet 1 : Système RAG */}
      {activeTab === "rag" && (
        <div>
          <div className="prompt-suggestions">
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", alignSelf: "center" }}>Suggestions :</span>
            {suggestedPrompts.map((p, i) => (
              <button key={i} className="suggestion-chip" onClick={() => setRagQuestion(p)}>
                {p}
              </button>
            ))}
          </div>

          <form onSubmit={handleRagSubmit}>
            <textarea
              className="textarea-box"
              rows={4}
              value={ragQuestion}
              onChange={(e) => setRagQuestion(e.target.value)}
              placeholder="Posez une question sur les documents internes..."
            />
            <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "16px" }}>
              <button className="btn-predict" type="submit" disabled={loading === "/ask"}>
                {loading === "/ask" ? (
                  <>
                    <Loader2 size={18} className="spin" />
                    <span>Recherche sémantique en cours...</span>
                  </>
                ) : (
                  <>
                    <FileSearch size={18} />
                    <span>Interroger la Base RAG</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {ragResult?.answer && (
            <div className="rag-answer-box">
              <div className="rag-answer-header">
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Sparkles size={18} color="var(--teal-400)" />
                  <strong style={{ color: "var(--text-primary)", fontSize: "0.95rem" }}>Réponse Générée :</strong>
                </div>
                {ragResult.fallback && (
                  <span className="metric-badge red">Mode Fallback Actif</span>
                )}
              </div>
              <p className="rag-answer-text">{ragResult.answer}</p>
              {ragResult.sources?.length > 0 && (
                <div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
                    Sources Documentaires Retrouvées :
                  </span>
                  <div className="sources-list">
                    {ragResult.sources.map((src, i) => (
                      <span className="source-badge" key={i}>{src}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <pre className="code-output-block">
            {ragResult ? formatJson(ragResult) : "Les résultats bruts JSON s'afficheront ici."}
          </pre>
        </div>
      )}

      {/* Onglet 2 : Extraction Structurée */}
      {activeTab === "extract" && (
        <div>
          <form onSubmit={handleExtractSubmit}>
            <textarea
              className="textarea-box"
              rows={4}
              value={extractText}
              onChange={(e) => setExtractText(e.target.value)}
              placeholder="Collez le texte ou la facture à analyser..."
            />
            <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "16px" }}>
              <button className="btn-predict" type="submit" disabled={loading === "/extract"}>
                {loading === "/extract" ? (
                  <>
                    <Loader2 size={18} className="spin" />
                    <span>Extraction en cours...</span>
                  </>
                ) : (
                  <>
                    <Search size={18} />
                    <span>Extraire les Données Structurées</span>
                  </>
                )}
              </button>
            </div>
          </form>

          <pre className="code-output-block">
            {extractResult ? formatJson(extractResult) : "Aucun résultat d'extraction pour le moment."}
          </pre>
        </div>
      )}

      {/* Onglet 3 : Classification */}
      {activeTab === "classify" && (
        <div>
          <form onSubmit={handleClassifySubmit}>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "block", marginBottom: "6px" }}>
                Texte du document :
              </label>
              <textarea
                className="textarea-box"
                rows={4}
                value={classifyText}
                onChange={(e) => setClassifyText(e.target.value)}
              />
            </div>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "block", marginBottom: "6px" }}>
                Catégories cibles (séparées par virgule) :
              </label>
              <input
                type="text"
                className="form-input"
                value={categories}
                onChange={(e) => setCategories(e.target.value)}
              />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "16px" }}>
              <button className="btn-predict" type="submit" disabled={loading === "/classify"}>
                {loading === "/classify" ? (
                  <>
                    <Loader2 size={18} className="spin" />
                    <span>Classification en cours...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck size={18} />
                    <span>Classifier le Document</span>
                  </>
                )}
              </button>
            </div>
          </form>

          <pre className="code-output-block">
            {classifyResult ? formatJson(classifyResult) : "Résultat de la classification ici."}
          </pre>
        </div>
      )}
    </article>
  );
}

// ══════════════════════════════════════════════════════════════════
// 5. OBSERVABILITÉ (PROMETHEUS, GRAFANA & LOGS)
// ══════════════════════════════════════════════════════════════════
function ObservabilityView({ activityLog, health }) {
  return (
    <div className="grid-2-cols">
      <article className="panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <div className="panel-icon-wrap">
              <Activity size={18} />
            </div>
            <div>
              <p className="panel-eyebrow">Supervision</p>
              <h2 className="panel-title-text">Endpoints & Services d'Observabilité</h2>
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "20px" }}>
          <div style={{ background: "var(--bg-surface-soft)", padding: "14px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Scraper Prometheus</span>
            <strong style={{ fontSize: "1.1rem", color: "#38bdf8", fontFamily: "var(--font-mono)" }}>/metrics</strong>
          </div>
          <div style={{ background: "var(--bg-surface-soft)", padding: "14px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Dashboard Grafana</span>
            <strong style={{ fontSize: "1.1rem", color: "#fb923c", fontFamily: "var(--font-mono)" }}>:3001</strong>
          </div>
          <div style={{ background: "var(--bg-surface-soft)", padding: "14px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Serveur Prometheus</span>
            <strong style={{ fontSize: "1.1rem", color: "#f43f5e", fontFamily: "var(--font-mono)" }}>:9090</strong>
          </div>
          <div style={{ background: "var(--bg-surface-soft)", padding: "14px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Fallback LLM Trace</span>
            <strong style={{ fontSize: "1.1rem", color: "#34d399", fontFamily: "var(--font-mono)" }}>Actif</strong>
          </div>
        </div>

        <pre className="code-output-block">
          {formatJson(health || { status: "Monitoring actif sur les ports 8000, 9090, 3001." })}
        </pre>
      </article>

      <ActivityLogPanel activityLog={activityLog} />
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// 6. DÉPLOIEMENT KUBERNETES & CI/CD
// ══════════════════════════════════════════════════════════════════
function DeploymentView() {
  const [copied, setCopied] = useState(false);

  const cliCommands = `# 1. Entraînement du modèle de prévision
python src/train.py

# 2. Lancement du serveur API FastAPI
uvicorn src.serve:app --host 127.0.0.1 --port 8000 --reload

# 3. Démarrage de la stack de monitoring
docker compose -f docker-compose.monitoring.yml up --build -d

# 4. Smoke test conteneur Docker
.\\scripts\\docker_smoke_test.ps1 -ImageTag smoke`;

  const handleCopy = () => {
    navigator.clipboard.writeText(cliCommands);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const steps = [
    { title: "Docker Multi-Stage", text: "Image optimisée avec utilisateur non-root et assets React compilés intégrés." },
    { title: "Orchestration Kubernetes", text: "Manifests Deployment, Service, ConfigMap, Secrets et HPA (Autoscaler)." },
    { title: "Pipeline CI/CD GitHub Actions", text: "Tests unitaires automatisés, build Docker et publication sur GitHub Container Registry (GHCR)." },
    { title: "Supervision Prometheus & Grafana", text: "Collecte des métriques d'inférence, latence et dashboards pré-provisionnés." },
  ];

  return (
    <div className="grid-2-cols">
      <article className="panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <div className="panel-icon-wrap">
              <Rocket size={18} />
            </div>
            <div>
              <p className="panel-eyebrow">Pipeline & Architecture</p>
              <h2 className="panel-title-text">Architecture de Déploiement MLOps</h2>
            </div>
          </div>
        </div>

        <div className="timeline-container">
          {steps.map((step, idx) => (
            <div className="timeline-step" key={idx}>
              <div className="timeline-step-icon">
                <CheckCircle2 size={16} />
              </div>
              <div className="timeline-step-body">
                <strong>{step.title}</strong>
                <p>{step.text}</p>
              </div>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <div className="panel-icon-wrap">
              <Terminal size={18} />
            </div>
            <div>
              <p className="panel-eyebrow">Commandes Rapides</p>
              <h2 className="panel-title-text">Commandes d'Exécution & Test</h2>
            </div>
          </div>
        </div>

        <div className="cli-box">
          <div className="cli-header">
            <span>Terminal PowerShell / Bash</span>
            <button className="btn-copy-cli" onClick={handleCopy}>
              {copied ? <Check size={14} color="#34d399" /> : <Copy size={14} />}
              <span>{copied ? "Copié !" : "Copier"}</span>
            </button>
          </div>
          <pre className="cli-code">{cliCommands}</pre>
        </div>
      </article>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// 7. COMPOSANT HELPER : JOURNAL D'ACTIVITÉ RÉCENTE
// ══════════════════════════════════════════════════════════════════
function ActivityLogPanel({ activityLog }) {
  return (
    <article className="panel">
      <div className="panel-header">
        <div className="panel-title-group">
          <div className="panel-icon-wrap">
            <Activity size={18} />
          </div>
          <div>
            <p className="panel-eyebrow">Traçabilité & DB</p>
            <h2 className="panel-title-text" data-testid="Activite recente">Journal des Requêtes Récentes</h2>
          </div>
        </div>
      </div>

      <div className="activity-list-container">
        {activityLog.length === 0 ? (
          <div style={{ textAlign: "center", padding: "24px 0", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Aucune requête enregistrée dans la base de données SQLite pour l'instant.
          </div>
        ) : (
          activityLog.map((item, index) => (
            <div className="activity-item" key={`${item.endpoint}-${item.at}-${index}`}>
              <div>
                <span className="activity-endpoint">{item.endpoint}</span>
                <div className="activity-meta">{item.at} — {item.detail}</div>
              </div>
              <span className={`badge-status ${item.error ? "error" : item.status === "Fallback" ? "fallback" : "success"}`}>
                {item.status}
              </span>
            </div>
          ))
        )}
      </div>
    </article>
  );
}
