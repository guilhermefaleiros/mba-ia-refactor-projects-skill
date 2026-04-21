import os


def _bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_config():
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise EnvironmentError("Missing required environment variables: SECRET_KEY")

    return {
        "SECRET_KEY": secret_key,
        "SQLALCHEMY_DATABASE_URI": os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///tasks.db"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "DEBUG": _bool_env("DEBUG", False),
        "BCRYPT_ROUNDS": int(os.environ.get("BCRYPT_ROUNDS", "12")),
        "TOKEN_MAX_AGE": int(os.environ.get("TOKEN_MAX_AGE", "86400")),
        "SMTP_HOST": os.environ.get("SMTP_HOST"),
        "SMTP_PORT": int(os.environ.get("SMTP_PORT", "587")),
        "SMTP_USER": os.environ.get("SMTP_USER"),
        "SMTP_PASSWORD": os.environ.get("SMTP_PASSWORD"),
        "SMTP_USE_TLS": _bool_env("SMTP_USE_TLS", True),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO").upper(),
        "PORT": int(os.environ.get("PORT", "5000")),
    }
