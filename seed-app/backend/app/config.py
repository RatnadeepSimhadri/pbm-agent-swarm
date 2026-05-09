from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./pbm.db"
    jwt_secret: str = "pbm-demo-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    model_config = {"env_prefix": "PBM_"}


settings = Settings()
