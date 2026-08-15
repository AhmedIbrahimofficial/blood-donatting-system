import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Core ──────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DATABASE_URL: str
    SECRET_KEY: str = secrets.token_hex(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── CORS ──────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8082,"
        "http://127.0.0.1:3000,http://127.0.0.1:8082,"
        "http://localhost:3001,http://localhost:5173"
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ── Firebase ──────────────────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "firebase-service-account.json"

    # ── Sentry ────────────────────────────────────────────────────────────
    SENTRY_DSN: str = ""

    # ── Redis / Celery ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # ── SendGrid ──────────────────────────────────────────────────────────
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@lifelink.org"
    SENDGRID_FROM_NAME: str = "LifeLink"

    # ── Cloudflare R2 / AWS S3 ────────────────────────────────────────────
    S3_BUCKET_NAME: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "auto"


settings = Settings()
