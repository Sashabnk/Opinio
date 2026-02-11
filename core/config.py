import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    REFERRAL_CODE: str = "default_ref"
    API_KEY: str = ""
    DB_PATH: str = "opinion.db"
    CHANNEL_ID: str = ""  # e.g., "@my_channel" or "-100..."
    
    API_BASE_URL: str = "https://openapi.opinion.trade/openapi"
    POLLING_INTERVAL: int = 60  # seconds
    PRICE_SPIKE_THRESHOLD: float = 5.0  # percentage

config = Settings()
