from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 60
    RESET_TOKEN_EXPIRE_MINUTES: int = 15
    API_KEY:str
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    FRONTEND_URL: str
    DB_USER :str
    DB_PASSWORD :str
    DB_HOST :str
    DB_PORT : int
    DB_NAME : str

    class Config:
        env_file = ".env"

settings = Settings()