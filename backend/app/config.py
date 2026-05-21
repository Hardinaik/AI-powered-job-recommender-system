from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 60
    RESET_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    IS_PRODUCTION: bool=False
    GROQ_API_KEY:str
    GEMINI_API_KEY: str
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    FRONTEND_URL: str
    DATABASE_URL:str

    class Config:
        env_file = ".env"

settings = Settings()