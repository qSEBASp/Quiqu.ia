from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    provider: str = "demo"
    henrik_api_key: str = ""
    henrik_base_url: str = "https://api.henrikdev.xyz"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    demo_match_count: int = 14
    frontend_origin: str = "http://localhost:3000"

    def model_post_init(self, __context) -> None:
        if not self.database_url:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            self.database_url = f"sqlite:///{(DATA_DIR / 'quiqu.db').as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
