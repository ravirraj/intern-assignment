import { useState, useEffect } from "react";
import { fetchRanking } from "../api";

export default function RankingTable() {
  const [rankings, setRankings] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const limit = 10;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchRanking(page, limit)
      .then((res) => {
        if (!cancelled) {
          setRankings(res.rankings);
          setTotal(res.total);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [page]);

  const totalPages = Math.ceil(total / limit);

  const getMedal = (rank) => {
    if (rank === 1) return "🥇";
    if (rank === 2) return "🥈";
    if (rank === 3) return "🥉";
    return rank;
  };

  return (
    <div className="card">
      <h2>Rankings</h2>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading">Loading rankings...</div>
      ) : rankings.length === 0 ? (
        <div className="empty">No rankings yet. Submit some transactions to get started.</div>
      ) : (
        <>
          <table className="ranking-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>User</th>
                <th>Total Points</th>
                <th>Consistency</th>
                <th>Composite Score</th>
              </tr>
            </thead>
            <tbody>
              {rankings.map((entry) => (
                <tr key={entry.userId} className={entry.rank <= 3 ? "top-three" : ""}>
                  <td className="rank-cell">{getMedal(entry.rank)}</td>
                  <td>{entry.username}</td>
                  <td className="points-cell">{entry.totalPoints.toLocaleString()}</td>
                  <td>{(entry.consistencyScore * 100).toFixed(1)}%</td>
                  <td className="composite-cell">{entry.compositeScore.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            <button
              className="btn btn-secondary"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span className="page-info">
              Page {page} of {totalPages || 1} ({total} users)
            </span>
            <button
              className="btn btn-secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
