from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/food_service"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "suppliers"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    data_ttl_days: int = 7

    # ── LLM provider selection ─────────────────────────────────────────────
    # Allowed values: "anthropic" | "openai" | "ollama"
    llm_provider: str = "anthropic"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # OpenAI (or any OpenAI-compatible endpoint)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""  # override for custom endpoints

    # Ollama (local)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    class Config:
        env_file = ".env"


settings = Settings()
