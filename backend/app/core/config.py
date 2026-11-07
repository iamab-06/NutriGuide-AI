"""
NutriGuide AI - Application Settings
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ROOT_DIR = _BACKEND_DIR.parent

_ENV_FILES = [
    str(_BACKEND_DIR / ".env"),
    str(_BACKEND_DIR / ".env.txt"),
    str(_ROOT_DIR / ".env"),
    ".env",
]


class Settings(BaseSettings):
    # App
    app_name: str = "NutriGuide AI"
    app_version: str = "1.0.0"
    debug: bool = True

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # API Keys
    gemini_api_key: str = ""  # No longer required; retained for backward compatibility
    usda_api_key: str = "DEMO_KEY"
    openfoodfacts_user_agent: str = "NutriGuideAI - Web - Version 1.0 - https://github.com/nutriguide-ai"

    # Ollama / Gemma 3 4B IT (local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout: int = 120  # seconds; first inference can be slow

    # Model
    model_weights_path: str = "models/nutriguide_classifier.pth"
    confidence_threshold: float = 0.70

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __repr__(self) -> str:
        masked_gemini = "***" if self.gemini_api_key else ""
        masked_usda = "***" if (self.usda_api_key and self.usda_api_key != "DEMO_KEY") else self.usda_api_key
        return (
            f"Settings(app_name={self.app_name!r}, "
            f"backend_host={self.backend_host!r}, "
            f"backend_port={self.backend_port!r}, "
            f"gemini_api_key={masked_gemini!r}, "
            f"usda_api_key={masked_usda!r})"
        )

    def __str__(self) -> str:
        return self.__repr__()


settings = Settings()
