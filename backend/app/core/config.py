from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent
env_file_path = app_dir/".env"

class Settings(BaseSettings):
    Hello_URL:str
    DATABASE_URL:str
    ACCESS_TOKEN_EXPIRY_MINUTES:int = 60
    SECRET_KEY:str
    ALGORITHM:str
    GEMINI_API_KEY:str

    model_config = SettingsConfigDict(env_file=env_file_path,env_file_encoding = "utf-8", extra = "ignore")
settings = Settings()