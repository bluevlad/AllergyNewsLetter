"""
AllergyNewsLetter 설정 관리 모듈
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 프로젝트 경로
    BASE_DIR: Path = Path(__file__).parent.parent

    # 네이버 API
    naver_client_id: str = Field(default="", env="NAVER_CLIENT_ID")
    naver_client_secret: str = Field(default="", env="NAVER_CLIENT_SECRET")

    # PubMed API (E-utilities)
    pubmed_api_key: str = Field(default="", env="PUBMED_API_KEY")
    pubmed_email: str = Field(default="", env="PUBMED_EMAIL")

    # Ollama (로컬 AI)
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field(default="qwen2.5:7b", env="OLLAMA_MODEL")

    # Claude API (선택적)
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")

    # Gmail SMTP
    gmail_address: str = Field(default="", env="GMAIL_ADDRESS")
    gmail_app_password: str = Field(default="", env="GMAIL_APP_PASSWORD")

    # 데이터베이스
    database_url: str = Field(
        default="sqlite:///./data/allergynewsletter.db",
        env="DATABASE_URL"
    )

    # 스케줄러 - 크롤링 (오전 7시)
    crawl_hour: int = Field(default=7, env="CRAWL_HOUR")
    crawl_minute: int = Field(default=0, env="CRAWL_MINUTE")

    # 스케줄러 - 뉴스레터 발송 (오전 8시)
    send_hour: int = Field(default=8, env="SEND_HOUR")
    send_minute: int = Field(default=0, env="SEND_MINUTE")

    # 로깅
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # 웹 서버
    web_host: str = Field(default="0.0.0.0", env="WEB_HOST")
    web_port: int = Field(default=4050, env="WEB_PORT")

    # API 인증
    api_secret_token: str = Field(default="", env="API_SECRET_TOKEN")

    # 이메일 인증
    verification_code_length: int = Field(default=6)
    verification_expiry_minutes: int = Field(default=10)
    max_verification_attempts: int = Field(default=5)

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환"""
    return Settings()


settings = get_settings()
