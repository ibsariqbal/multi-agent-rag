from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    demo_mode: bool = True
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    pinecone_api_key: str = ""
    pinecone_index: str = "multi-agent-rag"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    frontend_origins: str = "http://localhost:5173"
    max_file_mb: int = 15
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def origins(self):
        return [x.strip() for x in self.frontend_origins.split(",")]

@lru_cache
def get_settings():
    return Settings()

