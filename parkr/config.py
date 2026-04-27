from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://parkr:parkr@localhost:5432/parkrdb"

    class Config:
        env_file = ".env"


settings = Settings()