# Leaderboard System

A full-stack leaderboard where users earn points through transactions. Rankings combine total points earned with consistency (how regularly a user transacts) to produce a fair composite score.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL (via asyncpg) |
| Frontend | React 18, Vite |
| Rate Limiting | In-memory sliding window |
| Deployment | Render (backend), Vercel (frontend) |

## Architecture

```
React (Vite)          FastAPI              PostgreSQL
:5173 ──────────► :8000/api ──────────► asyncpg pool
   │                   │
   └─ REST (JSON) ─────┘
```

The backend is a stateless async FastAPI service. All mutable state lives in PostgreSQL. The frontend is a single-page React app served as static files.

## Database Schema

### `users`

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) PK | UUID, auto-generated |
| username | VARCHAR(50) UNIQUE | Set to `user_{first 8 chars of UUID}` on creation |
| created_at | TIMESTAMPTZ | Server default: `now()` |

### `transactions`

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) PK | UUID, auto-generated |
| user_id | VARCHAR(36) FK → users.id | |
| amount | INTEGER | Points awarded (1–10,000) |
| idempotency_key | VARCHAR(100) UNIQUE | Prevents duplicate processing |
| description | VARCHAR(255) | Nullable |
| created_at | TIMESTAMPTZ | Server default: `now()` |

### `user_stats`

| Column | Type | Notes |
|--------|------|-------|
| user_id | VARCHAR(36) PK FK → users.id | One row per user |
| total_points | BIGINT | Running total |
| transaction_count | INTEGER | Running count |
| distinct_days | INTEGER | Days with at least one transaction |
| first_transaction_date | DATE | |
| last_transaction_date | DATE | |

`user_stats` is updated atomically within the same database transaction as each new `transactions` row insert, using `SELECT ... FOR UPDATE` for row-level locking.

## Setup

### Prerequisites

- Python 3.12
- Node.js 18+
- PostgreSQL running locally

### 1. Database

```sql
CREATE DATABASE leaderboard;
```

### 2. Backend

```bash
cd backend
cp .env.example .env          # Edit with your PostgreSQL credentials
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
cp .env.example .env          # Set VITE_API_URL
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/leaderboard` | Async PostgreSQL connection string |
| `DATABASE_URL_SYNC` | `postgresql://postgres:postgres@localhost:5432/leaderboard` | Sync connection string (for Alembic) |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed frontend origins |
| `MAX_TRANSACTION_AMOUNT` | `10000` | Cap per single transaction |
| `MIN_TRANSACTION_AMOUNT` | `1` | Minimum points per transaction |
| `RATE_LIMIT_PER_MINUTE` | `10` | Max transactions per IP per minute |
| `RANKING_WEIGHT_POINTS` | `0.7` | Weight for total points in composite score |
| `RANKING_WEIGHT_CONSISTENCY` | `0.3` | Weight for consistency in composite score |
| `VITE_API_URL` | `http://localhost:8000` | Backend URL (frontend only) |

## API Endpoints

### `POST /transaction`

Record a transaction that awards points to a user.

**Request:**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 150,
  "idempotencyKey": "unique-key-123",
  "description": "Completed daily challenge"
}
```

**Response (201):**
```json
{
  "id": "...",
  "userId": "550e8400-...",
  "amount": 150,
  "idempotencyKey": "unique-key-123",
  "description": "Completed daily challenge",
  "createdAt": "2026-06-23T10:00:00Z",
  "duplicate": false
}
```

**Errors:**
- `400` — Validation failure (amount out of range, missing fields)
- `429` — Rate limit exceeded (10 requests/minute per IP)

### `GET /summary/{userId}`

Get a user's summary including total points, transaction count, and consistency score.

**Response (200):**
```json
{
  "userId": "...",
  "username": "user_550e8400",
  "totalPoints": 1500,
  "transactionCount": 23,
  "consistencyScore": 0.72,
  "activeDays": 16,
  "firstTransactionDate": "2026-01-15",
  "lastTransactionDate": "2026-06-23",
  "memberSince": "2026-01-15T08:30:00Z"
}
```

Returns `404` if user not found.

### `GET /ranking`

Get paginated leaderboard rankings.

**Query params:** `page` (default 1), `limit` (default 20, max 100)

**Response (200):**
```json
{
  "rankings": [
    {
      "rank": 1,
      "userId": "...",
      "username": "user_abc123",
      "totalPoints": 5000,
      "consistencyScore": 0.95,
      "compositeScore": 4750.0
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 20
}
```

### `GET /health`

Returns `{"status": "ok"}`.

## Ranking Logic

The composite score is:

```
compositeScore = (totalPoints × 0.7) + (consistencyScore × 1000 × 0.3)
```

**Consistency score** is defined as:

```
consistencyScore = distinctDaysWithTransactions / totalDaysSinceFirstTransaction
```

This is a value between 0.0 and 1.0. A user who transacts every day scores 1.0; a user who transacts once in a 30-day window scores ~0.033.

The consistency score is multiplied by 1000 to bring it to a comparable magnitude as total points before the 30% weight is applied.

Rankings are sorted by composite score descending, with total points as tiebreaker.

**Example:** A user with 5000 points and 0.95 consistency scores `5000×0.7 + 0.95×1000×0.3 = 3500 + 285 = 3785`.

## Duplicate Prevention

Three layers prevent duplicate transactions:

1. **Client-generated idempotency key.** The frontend builds a deterministic key per submission: `${userId}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`. This ensures each UI submission gets a unique key.

2. **Fast-path check.** Before inserting, the service queries for an existing transaction with the same `idempotency_key`. If found, it returns the existing record with `duplicate: true` and HTTP 200.

3. **Database constraint.** A `UNIQUE` constraint on `idempotency_key` in the `transactions` table prevents duplicate rows even if concurrent requests bypass the fast-path check.

## Concurrency Handling

Each transaction modifies the `user_stats` row for that user (incrementing `total_points`, `transaction_count`, and potentially `distinct_days`). To prevent lost updates under concurrent requests:

- The service executes `SELECT ... FOR UPDATE` on the `user_stats` row within a database transaction. This acquires a pessimistic row-level lock, serializing concurrent transactions for the same user.
- The transaction row insert and the stats update are committed atomically — both succeed or both fail.

## Abuse Prevention

- **Amount cap.** Each transaction is limited to 10,000 points (enforced by Pydantic validation).
- **Rate limiting.** Max 10 transactions per IP per minute using an in-memory sliding window (`SlidingWindowLimiter` in `main.py`).
- **Input validation.** All fields validated via Pydantic schemas: `amount` must be 1–10,000, `idempotencyKey` non-empty and max 100 chars, `userId` non-empty.

## Assumptions

- Users are auto-created on first transaction (username = `user_{first 8 chars of UUID}`).
- No authentication — this is a demo. In production, JWT auth would be required.
- Rate limiter is in-memory and resets on server restart. In production, use Redis.
- The consistency score formula assumes all days are equally weighted (no weekends/holidays adjustment).
- Database tables are auto-created at startup via `Base.metadata.create_all` (no migration step required).

## Trade-offs and Limitations

| Decision | Trade-off |
|----------|-----------|
| In-memory rate limiter | Simple but lost on restart; not shared across instances |
| Composite score computed in Python | Correctness over performance; works at small scale but won't scale to millions of users |
| No authentication | Simplifies demo but任何人都 can submit transactions for any userId |
| `SELECT ... FOR UPDATE` | Correct concurrency but reduces throughput under high contention for a single user |
| Auto-create users on first transaction | Convenient but means any userId string is accepted without pre-registration |
| SQLAlchemy `create_all` at startup | No migration history; schema changes require manual intervention |

## Deployment

### Backend (Render)

1. Push code to GitHub
2. Create a Render Web Service from the repo
3. Set `DATABASE_URL` to a Render-managed PostgreSQL connection string
4. Render builds from `backend/Dockerfile` (Python 3.12-slim) and runs `uvicorn main:app`

### Frontend (Vercel)

1. Deploy the `frontend/` directory
2. Set `VITE_API_URL` to the Render backend URL
3. Vercel serves the built React app as static files
4. `vercel.json` rewrites all routes to `index.html` for SPA routing

## Folder Structure

```
intern-assignment/
├── .gitignore
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── config.py              # Pydantic settings (env vars)
│   ├── database.py            # Async engine, session, init_db
│   ├── main.py                # FastAPI app, CORS, rate limiter, lifespan
│   ├── models.py              # SQLAlchemy models (User, Transaction, UserStats)
│   ├── requirements.txt
│   ├── schemas.py             # Pydantic request/response models
│   ├── routes/
│   │   ├── transaction.py     # POST /transaction
│   │   ├── summary.py         # GET /summary/{userId}
│   │   └── ranking.py         # GET /ranking
│   └── services/
│       ├── transaction_service.py  # Transaction creation logic
│       └── ranking_service.py      # Summary + ranking computation
└── frontend/
    ├── index.html
    ├── package.json
    ├── vercel.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx            # Tab layout (Rankings, Summary, Transaction)
        ├── api.js             # Fetch wrappers for all endpoints
        ├── components/
        │   ├── RankingTable.jsx   # Paginated leaderboard table
        │   ├── UserSummary.jsx    # User lookup + stats grid
        │   └── TransactionForm.jsx # Transaction submission form
        └── styles/
            └── App.css
```

## Future Improvements

- **Authentication.** JWT-based auth so users can only submit for their own account.
- **Redis-backed rate limiting.** Shared across instances, survives restarts.
- **Materialized views or caching.** Precompute rankings to avoid full-table scans on every request.
- **Database migrations.** Replace `create_all` with Alembic migrations for safe schema evolution.
- **Event sourcing for transactions.** Append-only log with projections for stats, enabling auditability and replay.
- **Webhooks or SSE.** Push ranking updates to the frontend instead of polling.
- **Admin dashboard.** View system health, transaction volume, and rate limit hits.
- **Pagination for summary lookup.** Currently returns a single user; could extend to batch lookups.
