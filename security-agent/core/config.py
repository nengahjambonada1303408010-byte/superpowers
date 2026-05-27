from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    service_api_key: str = Field("change-this-secret-key", alias="SERVICE_API_KEY")
    model: str = Field("claude-opus-4-7", alias="MODEL")
    max_tokens: int = Field(8192, alias="MAX_TOKENS")
    rate_limit_per_minute: int = Field(60, alias="RATE_LIMIT_PER_MINUTE")
    environment: str = Field("development", alias="ENVIRONMENT")
    max_agent_iterations: int = Field(10, alias="MAX_AGENT_ITERATIONS")
    allowed_file_extensions: str = Field(
        ".py,.php,.js,.ts,.java,.go,.rb,.cs,.cpp,.c,.h,.html,.css,.json,.yaml,.yml,.env,.conf,.xml",
        alias="ALLOWED_FILE_EXTENSIONS",
    )

    @property
    def allowed_extensions_set(self) -> set[str]:
        return set(self.allowed_file_extensions.split(","))


settings = Settings()
