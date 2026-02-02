"""
데이터베이스 테스트
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import (
    init_db, get_session,
    ArticleRepository, RecipientRepository,
    Article, Recipient,
    ContentType, AllergyCategory, RecipientGroup
)


@pytest.fixture(scope="module")
def setup_db():
    """테스트용 인메모리 DB 설정"""
    init_db("sqlite:///:memory:")
    yield
    # 테스트 후 정리 불필요 (인메모리)


class TestArticleRepository:
    """ArticleRepository 테스트"""

    def test_create_article(self, setup_db):
        """기사 생성 테스트"""
        with get_session() as session:
            article_data = {
                "title": "테스트 기사",
                "description": "테스트 내용",
                "link": f"https://example.com/{datetime.now().timestamp()}",
                "content_type": ContentType.NEWS,
            }

            article = ArticleRepository.create(session, article_data)

            assert article.id is not None
            assert article.title == "테스트 기사"
            assert article.content_hash is not None

    def test_exists_by_link(self, setup_db):
        """링크 존재 확인 테스트"""
        unique_link = f"https://example.com/exists-{datetime.now().timestamp()}"

        with get_session() as session:
            # 생성 전
            assert ArticleRepository.exists_by_link(session, unique_link) is False

            # 생성
            ArticleRepository.create(session, {
                "title": "테스트",
                "description": "내용",
                "link": unique_link,
            })

        with get_session() as session:
            # 생성 후
            assert ArticleRepository.exists_by_link(session, unique_link) is True

    def test_update_analysis(self, setup_db):
        """분석 결과 업데이트 테스트"""
        with get_session() as session:
            article = ArticleRepository.create(session, {
                "title": "분석 테스트",
                "description": "내용",
                "link": f"https://example.com/analysis-{datetime.now().timestamp()}",
            })
            article_id = article.id

        with get_session() as session:
            ArticleRepository.update_analysis(
                session,
                article_id,
                AllergyCategory.CLINICAL,
                "요약 텍스트",
                0.85
            )

        with get_session() as session:
            article = session.query(Article).filter(Article.id == article_id).first()
            assert article.category == AllergyCategory.CLINICAL
            assert article.summary == "요약 텍스트"
            assert article.importance_score == 0.85
            assert article.is_processed is True


class TestRecipientRepository:
    """RecipientRepository 테스트"""

    def test_create_recipient(self, setup_db):
        """수신자 생성 테스트"""
        with get_session() as session:
            recipient = RecipientRepository.create(
                session,
                email=f"test-{datetime.now().timestamp()}@example.com",
                name="테스트 사용자",
                group=RecipientGroup.ALL
            )

            assert recipient.id is not None
            assert recipient.is_active is True

    def test_get_all_active(self, setup_db):
        """활성 수신자 조회 테스트"""
        with get_session() as session:
            # 활성 수신자 생성
            RecipientRepository.create(
                session,
                email=f"active-{datetime.now().timestamp()}@example.com",
                name="활성 사용자",
                group=RecipientGroup.ALL
            )

            recipients = RecipientRepository.get_all_active(session)
            assert len(recipients) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
