"""
NutriGuide AI - Application Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    app_name: str = "NutriGuide AI"
    app_version: str = "1.0.0"
    debug: bool = True

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # API Keys
    gemini_api_key: str = ""
    usda_api_key: str = "DEMO_KEY"
    openfoodfacts_user_agent: str = "NutriGuideAI/1.0"

    # Model
    model_weights_path: str = "models/nutriguide_classifier.pth"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
