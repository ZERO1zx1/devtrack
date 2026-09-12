"""Application configuration, split by environment (12-factor friendly).

Select with the ``CONFIG`` environment variable::

    CONFIG=production python run.py

or for tests::

    pytest   # pick up TestingConfig automatically
"""

import os


def _load_env_file(path=".env"):
    """Tiny dependency-free .env loader (KEY=VALUE lines, # comments).

    Existing environment variables always win; this only fills in what is
    missing so shell exports keep overriding the file.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip()
                if value.startswith(('"', "'")) and value.endswith(('"', "'")) and len(value) >= 2:
                    value = value[1:-1]
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


_load_env_file()


def _env_bool(name, default="0"):
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    """Shared defaults for every environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "devtrack-dev-secret")
    INSTANCE_DIR = os.environ.get("INSTANCE_DIR", "instance")
    DATABASE = os.path.join(INSTANCE_DIR, "devtrack.db")

    # Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Public base URL used for absolute links in emails.
    APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:5001")

    # SMTP (password reset email delivery). Leave SMTP_HOST empty to disable
    # real delivery; the mailer then logs the message to the server log.
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_MAIL_FROM = os.environ.get("SMTP_MAIL_FROM", "") or os.environ.get("SMTP_USERNAME", "")
    SMTP_USE_TLS = _env_bool("SMTP_USE_TLS", "1")
    SMTP_USE_SSL = _env_bool("SMTP_USE_SSL", "0")


class DevConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True
    # TestConfig overrides the database path at the last moment from conftest,
    # but keep a sensible default for ad-hoc runs.
    DATABASE = os.environ.get(
        "TEST_DATABASE", os.path.join(BaseConfig.INSTANCE_DIR, "devtrack-test.db")
    )


class ProdConfig(BaseConfig):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SESSION_COOKIE_SECURE = True


CONFIG_MAP = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig,
}


def get_config(name=None):
    """Return the config class for ``name`` (or ``development`` default).

    Production demands an explicit secret; validated here (at selection time,
    not import time) so importing this module never fails spuriously.
    """
    resolved = name or "development"
    if resolved == "production" and not os.environ.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY environment variable is required in production.")
    return CONFIG_MAP.get(resolved, DevConfig)