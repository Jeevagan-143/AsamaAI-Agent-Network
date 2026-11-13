
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Asama.ai")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:password@localhost:5432/asama_ai"
    )

    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "BAAI/bge-small-en-v1.5"
    )

    EMBEDDING_DIMENSIONS: int = 384

    RERANK_THRESHOLD: float = float(
        os.getenv("RERANK_THRESHOLD", "0.75")
    )

    MAX_ROUTING_CANDIDATES: int = int(
        os.getenv("MAX_ROUTING_CANDIDATES", "50")
    )

    MAX_NOTIFICATIONS_PER_POST: int = int(
        os.getenv("MAX_NOTIFICATIONS_PER_POST", "5")
    )

    AGENT_API_KEY_SECRET: str = os.getenv(
        "AGENT_API_KEY_SECRET",
        "development-only-secret"
    )


settings = Settings()
