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
        "dvwa,vuln-node-api,weak-ssh,localhost,127.0.0.1,"
        "cybersim-dvwa,cybersim-vuln-node,cybersim-weak-ssh"
    )

    @property
    def allowlist(self) -> set[str]:
        return {h.strip().lower() for h in self.target_allowlist.split(",") if h.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
