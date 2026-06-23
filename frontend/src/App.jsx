import { useState, useEffect } from "react";
import TransactionForm from "./components/TransactionForm";
import UserSummary from "./components/UserSummary";
import RankingTable from "./components/RankingTable";
import { checkHealth } from "./api";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState("ranking");
  const [refreshKey, setRefreshKey] = useState(0);
  const [backendStatus, setBackendStatus] = useState("checking");

  useEffect(() => {
    const check = async () => {
      try {
        const ok = await checkHealth();
        setBackendStatus(ok ? "online" : "offline");
      } catch {
        setBackendStatus("offline");
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleTransactionSuccess = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Leaderboard</h1>
        <p className="subtitle">Track points, consistency, and rankings</p>
      </header>

      <nav className="tabs">
        <button
          className={`tab ${activeTab === "ranking" ? "active" : ""}`}
          onClick={() => setActiveTab("ranking")}
        >
          Rankings
        </button>
        <button
          className={`tab ${activeTab === "summary" ? "active" : ""}`}
          onClick={() => setActiveTab("summary")}
        >
          User Summary
        </button>
        <button
          className={`tab ${activeTab === "transaction" ? "active" : ""}`}
          onClick={() => setActiveTab("transaction")}
        >
          Submit Transaction
        </button>
      </nav>

      <main className="content">
        {activeTab === "ranking" && <RankingTable key={refreshKey} />}
        {activeTab === "summary" && <UserSummary />}
        {activeTab === "transaction" && (
          <TransactionForm onSuccess={handleTransactionSuccess} />
        )}
      </main>

      <footer className="status-badge">
        <span className={`status-dot ${backendStatus}`} />
        <span className="status-text">
          {backendStatus === "checking" && "Checking backend..."}
          {backendStatus === "online" && "Backend is live"}
          {backendStatus === "offline" && "Backend is down"}
        </span>
        <a
          className="status-link"
          href={`${API_BASE}/health`}
          target="_blank"
          rel="noopener noreferrer"
        >
          Check here
        </a>
      </footer>
    </div>
  );
}
