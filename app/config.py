from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: str = "/data/db.sqlite"
    workshop_dir: str = "/data/workshop"
    # Absolute path on the HOST machine - used when spawning SteamCMD containers
    # via Docker socket (DinD). Must match the host-side path of ./data.
    host_data_dir: str = "/home/ubuntu/zomboid-mod-id-extracter/data"
    steamcmd_image: str = "sonroyaalmerol/steamcmd-arm64"
    steamcmd_entrypoint: str = "/home/steam/steamcmd/steamcmd.sh"

    class Config:
        env_file = ".env"


settings = Settings()
