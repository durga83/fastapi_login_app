from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MINIO_URL: str = "http://localhost:4003"
    MINIO_ACCESS_KEY: str = "xtrimchat"
    MINIO_SECRET_KEY: str = "xtrimchat"
    BUCKET_NAME: str = "knowledge-hub"

    class Config:
        env_file = ".env"