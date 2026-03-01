from pydantic_settings import BaseSettings, SettingsConfigDict

SYSTEM_PROMPT = (
    "You are a helpful AI search assistant. "
    "Provide concise, well-researched answers. "
    "Do not include citation numbers or reference markers in your response."
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    perplexity_api_key: str
    cors_origins: list[str] = ["*"]


settings = Settings()  # type: ignore[call-arg]
