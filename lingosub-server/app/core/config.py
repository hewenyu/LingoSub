import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)


class Settings(BaseSettings):
    # .env 文件中变量的前缀，例如 LINGOSUB_API_KEY
    # model_config = SettingsConfigDict(env_prefix='LINGOSUB_')

    # 直接读取环境变量
    API_KEY: str
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    TEMP_FILE_DIR: str = "temp_files"
    RESULT_FILE_DIR: str = "result_files"

    # OpenAI API settings
    OPENAI_API_KEY: str = "your_openai_api_key_here"
    OPENAI_BASE_URL: Optional[str] = None

    # 如果 .env 文件存在，则从中加载
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')


settings = Settings()