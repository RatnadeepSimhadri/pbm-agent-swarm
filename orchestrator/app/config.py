from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-6"
    seed_app_path: str = "../seed-app"
    workspace_base: str = "./workspaces"
    use_mock: bool = True

    model_config = {"env_prefix": ""}


settings = Settings()
