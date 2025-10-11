from typing import ClassVar

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseModel):
    api_key: SecretStr = Field(default=SecretStr(""), description="API key for OpenAI")
    embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model to use"
    )


class Neo4jSettings(BaseModel):
    uri: str = Field(default="bolt://localhost:7687", description="URI for Neo4j database")
    username: str = Field(default="neo4j", description="Username for Neo4j database")
    password: SecretStr = Field(default=SecretStr(""), description="Password for Neo4j database")


class QdrantSettings(BaseModel):
    url: str = Field(default="http://localhost:6333", description="URL for Qdrant instance")
    api_key: SecretStr = Field(default=SecretStr(""), description="API key for Qdrant instance")
    collection_name: str = Field(
        default="biomedical_papers", description="Collection name for Qdrant instance"
    )


class PubMedSettings(BaseModel):
    email: SecretStr = Field(default=SecretStr(""), description="Email for PubMed API")
    api_key: SecretStr = Field(default=SecretStr(""), description="API key for PubMed API")


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Use .env file or environment variables to configure.
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=[".env"],
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
        frozen=True,
    )

    openai: OpenAISettings = OpenAISettings()
    neo4j: Neo4jSettings = Neo4jSettings()
    qdrant: QdrantSettings = QdrantSettings()
    pubmed: PubMedSettings = PubMedSettings()


# Global settings instance
settings = Settings()
