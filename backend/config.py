from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leaderboard"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/leaderboard"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    MAX_TRANSACTION_AMOUNT: int = 10000
    MIN_TRANSACTION_AMOUNT: int = 1
    RATE_LIMIT_PER_MINUTE: int = 10
    RANKING_WEIGHT_POINTS: float = 0.7
    RANKING_WEIGHT_CONSISTENCY: float = 0.3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
