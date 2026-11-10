from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    database_url: str = "postgresql://localhost/eletrobar"
    allowed_origins: str = "http://localhost:5500,http://127.0.0.1:5500"

    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    redis_url: str = ""
    rate_limit_per_minute: int = 20

    n8n_webhook_url: str = ""
    n8n_webhook_secret: str = ""

    ingest_api_key: str = ""

    rag_top_k: int = 5
    chat_history_limit: int = 10

    @property
    def origin_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
