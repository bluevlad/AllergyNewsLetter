"""
AllergyNewsLetter 웹 서버 실행 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.database import init_db

if __name__ == "__main__":
    import uvicorn
    import logging

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    logger = logging.getLogger(__name__)

    # 로그 디렉토리 생성
    (settings.BASE_DIR / "logs").mkdir(exist_ok=True)

    # 데이터베이스 초기화
    logger.info("데이터베이스 초기화...")
    init_db(settings.database_url)

    # 웹 서버 실행
    logger.info(f"웹 서버 시작: http://{settings.web_host}:{settings.web_port}")
    uvicorn.run(
        "src.web.app:app",
        host=settings.web_host,
        port=settings.web_port,
        reload=False,
        log_level="info"
    )
