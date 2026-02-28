from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: str = "/data/db.sqlite"
    workshop_dir: str = "/data/workshop"
    steamcmd_image: str = "sonroyaalmerol/steamcmd-arm64"

    class Config:
        env_file = ".env"


settings = Settings()
