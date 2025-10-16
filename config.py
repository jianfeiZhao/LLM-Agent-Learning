"""
配置管理模块
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = "https://aigc.sankuai.com/v1/openai/native"
    search_api_key: Optional[str] = None
    llm_provider: str = "openai"  # 支持: openai, mock
    llm_model: str = "gpt-3.5-turbo"
    prompt_config_file: str = "prompt_config.json"
    # 重试/限流配置
    llm_max_retries: int = 5
    llm_retry_wait_seconds: float = 10.0
    appid_list: List[str] = [
        "1731880735004692535",
        "1889146223668690996",
        "1734415800163192918",
        "1783462889744248849",
        "1919947539366387808",
        "1919947698544418851",
        "1796110759362199605",
        "1794984524074676265",
        "1792464990918938657",
        "1789931624457855004",
        "1789903374117359714",
        "1787822145012584505",
        "1785146944130732056",
        "1785146918596018242",
        "1785146889328074779",
        "1785146861184548942",
        "1785146832369369093",
        "1783462795028553741",
        "1734834926589104200"
    ]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

# 全局配置实例
settings = Settings()
