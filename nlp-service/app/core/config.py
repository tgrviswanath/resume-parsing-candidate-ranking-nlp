from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "Resume Parsing & Candidate Ranking NLP Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001
    SPACY_MODEL: str = "en_core_web_sm"
    EMBED_MODEL: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"


settings = Settings()
