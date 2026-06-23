const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function submitTransaction({ userId, amount, idempotencyKey, description }) {
  const res = await fetch(`${API_BASE}/transaction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userId, amount, idempotencyKey, description }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Transaction failed");
  }
  return res.json();
}

export async function fetchSummary(userId) {
  const res = await fetch(`${API_BASE}/summary/${userId}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to fetch summary");
  }
  return res.json();
}

export async function fetchRanking(page = 1, limit = 20) {
  const res = await fetch(`${API_BASE}/ranking?page=${page}&limit=${limit}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to fetch ranking");
  }
  return res.json();
}
