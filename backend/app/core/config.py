from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent
env_file_path = app_dir/".env"

class Settings(BaseSettings):
    Hello_URL:str
    DATABASE_URL:str

    model_config = SettingsConfigDict(env_file=env_file_path,env_file_encoding = "utf-8", extra = "ignore")
settings = Settings()