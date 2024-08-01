from pydantic_settings import BaseSettings


class Config(BaseSettings):
    SPORT_RADAR_API_KEY: str

    class Config:
        env_file = ".env"
