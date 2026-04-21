import os
import logging


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DATABASE_URL = os.environ.get("DATABASE_URL", "loja.db")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
    PORT = int(os.environ.get("PORT", "5000"))

    @classmethod
    def validate(cls):
        required = ["SECRET_KEY"]
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {missing}. "
                "Copy .env.example to .env and fill in the values."
            )

    @classmethod
    def configure_logging(cls):
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL, logging.INFO),
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )
