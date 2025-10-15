"""
配置管理模块
"""
import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    openai_api_key: Optional[str] = None
    search_api_key: Optional[str] = None
    llm_provider: str = "openai"  # 支持: openai, mock
    llm_model: str = "gpt-3.5-turbo"
    prompt_config_file: str = "prompt_config.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 全局配置实例
settings = Settings()
