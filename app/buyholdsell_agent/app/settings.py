import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class AgentSettings(BaseSettings):
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    azure_endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    azure_api_version: str = Field(..., description="Azure OpenAI API version")
    azure_api_key: str = Field(..., description="Azure OpenAI API key")
    model_config = SettingsConfigDict(
        env_file=os.path.dirname(os.path.realpath(__file__)) + "/.env",
        env_file_encoding="utf-8",
    )