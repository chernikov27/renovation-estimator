from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = "sqlite:///data/app.db"
    price_list_seed_path: Path = ROOT_DIR / "data" / "price_list.seed.v2.json"
    uploads_dir: Path = ROOT_DIR / "data" / "uploads"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
