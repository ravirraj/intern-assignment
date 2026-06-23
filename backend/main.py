from contextlib import asynccontextmanager
from collections import defaultdict
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from config import settings
from database import init_db
from routes.transaction import router as transaction_router
from routes.summary import router as summary_router
from routes.ranking import router as ranking_router


# In-memory rate limiter: sliding window per user per minute
class SlidingWindowLimiter:
    def __init__(self):
        self.windows: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        self.windows[key] = [t for t in self.windows[key] if t > cutoff]
        if len(self.windows[key]) >= max_requests:
            return False
        self.windows[key].append(now)
        return True


limiter = SlidingWindowLimiter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Leaderboard API",
    description="A leaderboard system with transaction tracking, user summaries, and fair ranking.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/transaction" and request.method == "POST":
        client_ip = request.client.host if request.client else "unknown"
        # Try to extract userId from body for per-user limiting
        # Fallback to IP-based limiting
        rate_key = f"user:{client_ip}"
        if not limiter.is_allowed(rate_key, settings.RATE_LIMIT_PER_MINUTE):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Max 10 transactions per minute."},
            )
    response = await call_next(request)
    return response


app.include_router(transaction_router)
app.include_router(summary_router)
app.include_router(ranking_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
