import { useState } from "react";
import TransactionForm from "./components/TransactionForm";
import UserSummary from "./components/UserSummary";
import RankingTable from "./components/RankingTable";

export default function App() {
  const [activeTab, setActiveTab] = useState("ranking");
  const [refreshKey, setRefreshKey] = useState(0);

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
    </div>
  );
}
