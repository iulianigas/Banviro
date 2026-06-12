from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://banviro:banviro@localhost:5432/banviro"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"

    # AI layer
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_timeout_seconds: int = 120
    ollama_num_predict: int = 200
    ollama_keep_alive: str = "30m"
    ollama_temperature: float = 0.2
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "banviro_transactions"
    qdrant_vector_size: int = 768
    ai_enabled: bool = True
    phoenix_enabled: bool = True
    phoenix_project_name: str = "banviro"
    phoenix_endpoint: str = "http://localhost:6006"
    phoenix_collector_endpoint: str = "http://localhost:4317"
    phoenix_collector_protocol: str = "grpc"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
