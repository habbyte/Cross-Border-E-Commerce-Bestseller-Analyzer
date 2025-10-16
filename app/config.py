from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    firecrawl_api_key: str = Field(alias="FIRECRAWL_API_KEY")

    def model_post_init(self, __context) -> None:
        # 將沒有指定驅動的 Postgres 連線字串，統一轉成 psycopg v3 驅動
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif self.database_url.startswith("postgresql://") and "+psycopg" not in self.database_url:
            self.database_url = self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    class Config:
        env_file = ".env"


settings = Settings()