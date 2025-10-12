from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # -------------------------
    # App
    # -------------------------
    APP_NAME: str = config("APP_NAME", default="MediumClone")

    # -------------------------
    # Database
    # -------------------------
    POSTGRES_USER: str = config("POSTGRES_USER", default="postgres")
    POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD")
    POSTGRES_DB: str = config("POSTGRES_DB")
    POSTGRES_HOST: str = config("POSTGRES_HOST", default="localhost")
    POSTGRES_PORT: int = config("POSTGRES_PORT", default=5432, cast=int)

    DATABASE_URL: str = (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # -------------------------
    # JWT & Auth
    # -------------------------
    JWT_SECRET_KEY: str = config("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = config("JWT_ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config(
        "ACCESS_TOKEN_EXPIRE_MINUTES", default=60, cast=int
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = config(
        "REFRESH_TOKEN_EXPIRE_DAYS", default=7, cast=int
    )

    # -------------------------
    # Redis / Celery
    # -------------------------
    REDIS_HOST: str = config("REDIS_HOST", default="localhost")
    REDIS_PORT: int = config("REDIS_PORT", default=6379, cast=int)
    REDIS_DB: int = config("REDIS_DB", default=0, cast=int)
    CELERY_BROKER_URL: str = config(
        "CELERY_BROKER_URL", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )
    CELERY_RESULT_BACKEND: str = config(
        "CELERY_RESULT_BACKEND", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )

    # -------------------------
    # AWS / S3
    # -------------------------
    AWS_ACCESS_KEY_ID: str = config("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY: str = config("AWS_SECRET_ACCESS_KEY", default="")
    AWS_REGION: str = config("AWS_REGION", default="us-east-1")
    AWS_S3_BUCKET_NAME: str = config("AWS_S3_BUCKET_NAME", default="")
    AWS_S3_ENDPOINT: str = config(
        "AWS_S3_ENDPOINT", default=f"https://s3.{AWS_REGION}.amazonaws.com"
    )

    # -------------------------
    # Email (optional)
    # -------------------------
    SMTP_HOST: str = config("SMTP_HOST", default="smtp.gmail.com")
    SMTP_PORT: int = config("SMTP_PORT", default=587, cast=int)
    SMTP_USER: str = config("SMTP_USER", default="")
    SMTP_PASSWORD: str = config("SMTP_PASSWORD", default="")
    MAIL_FROM: str = config("MAIL_FROM", default="")
    MAIL_FROM_NAME: str = config("MAIL_FROM_NAME", default="Medium Clone")

    # -------------------------
    # CORS
    # -------------------------
    BACKEND_CORS_ORIGINS = config(
        "BACKEND_CORS_ORIGINS", default="http://localhost:3000", cast=Csv()
    )


settings = Settings()
