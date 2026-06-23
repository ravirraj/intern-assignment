import { useState } from "react";
import { submitTransaction } from "../api";

export default function TransactionForm({ onSuccess }) {
  const [userId, setUserId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    const idempotencyKey = `${userId}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

    try {
      const res = await submitTransaction({
        userId,
        amount: parseInt(amount, 10),
        idempotencyKey,
        description: description || null,
      });
      setResult(res);
      setAmount("");
      setDescription("");
      onSuccess?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Submit Transaction</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="userId">User ID</label>
          <input
            id="userId"
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Enter user UUID"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="amount">Points (1 - 10,000)</label>
          <input
            id="amount"
            type="number"
            min="1"
            max="10000"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="Enter points to award"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="description">Description (optional)</label>
          <input
            id="description"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Completed daily challenge"
            maxLength={255}
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Submitting..." : "Submit Transaction"}
        </button>
      </form>

      {result && (
        <div className={`alert ${result.duplicate ? "alert-warn" : "alert-success"}`}>
          {result.duplicate
            ? "Duplicate transaction detected — returned existing record."
            : `Transaction recorded: ${result.amount} points for ${result.userId}`}
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}
    </div>
  );
}
