from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://cybersim:cybersim@db:5432/cybersim"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    securewatch_webhook_url: str = ""
    securewatch_api_key: str = ""

    # Only these destinations may ever be attacked. Everything else is rejected.
    target_allowlist: str = (
        "dvwa,vuln-node-api,mini-vuln-app,weak-ssh,juice-shop,juice-shop-target,"
        "localhost,127.0.0.1,cybersim-dvwa,cybersim-vuln-node,"
        "cybersim-mini-vuln,cybersim-weak-ssh,cybersim-juice-shop"
    )

    @property
    def async_database_url(self) -> str:
        """Return a SQLAlchemy async URL.

        Railway's Postgres plugin exposes DATABASE_URL as postgresql://...
        SQLAlchemy interprets that as the sync psycopg2 driver. CyberSim uses
        async SQLAlchemy sessions, so normalize it to postgresql+asyncpg://...
        automatically.
        """
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url

    @property
    def allowlist(self) -> set[str]:
        return {h.strip().lower() for h in self.target_allowlist.split(",") if h.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
