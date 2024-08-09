from pydantic_settings import BaseSettings
from typing import Optional


class Config(BaseSettings):
    ENV: Optional[str] = "dev"
    S3_BUCKET: Optional[str] = "lineal-world-title"
