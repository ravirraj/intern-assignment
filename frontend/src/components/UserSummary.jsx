import { useState } from "react";
import { fetchSummary } from "../api";

export default function UserSummary() {
  const [userId, setUserId] = useState("");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSummary(null);

    try {
      const res = await fetchSummary(userId);
      setSummary(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>User Summary</h2>
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="Enter user UUID"
          required
        />
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Loading..." : "Look Up"}
        </button>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {summary && (
        <div className="summary-grid">
          <div className="stat-card">
            <span className="stat-label">Username</span>
            <span className="stat-value">{summary.username}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total Points</span>
            <span className="stat-value highlight">{summary.totalPoints.toLocaleString()}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Transactions</span>
            <span className="stat-value">{summary.transactionCount}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Consistency Score</span>
            <span className="stat-value">{(summary.consistencyScore * 100).toFixed(1)}%</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Active Days</span>
            <span className="stat-value">{summary.activeDays}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Member Since</span>
            <span className="stat-value">
              {new Date(summary.memberSince).toLocaleDateString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
