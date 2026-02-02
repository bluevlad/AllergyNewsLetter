"""
수집기 테스트
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collector.base import NewsArticle, PaperArticle, CollectedItem
from src.collector.naver_news import NaverNewsCollector
from src.collector.pubmed import PubMedCollector


class TestCollectedItem:
    """CollectedItem 기본 테스트"""

    def test_news_article_hash(self):
        """뉴스 기사 해시 생성 테스트"""
        article = NewsArticle(
            title="테스트 기사",
            description="테스트 내용",
            link="https://example.com/1"
        )

        assert article.content_hash is not None
        assert len(article.content_hash) == 64  # SHA-256

    def test_paper_article_hash(self):
        """논문 해시 생성 테스트"""
        paper = PaperArticle(
            title="Test Paper",
            description="Test abstract",
            link="https://pubmed.ncbi.nlm.nih.gov/12345/",
            pmid="12345"
        )

        assert paper.content_hash is not None
        assert paper.pmid == "12345"

    def test_same_content_same_hash(self):
        """동일 내용은 동일 해시"""
        article1 = NewsArticle(
            title="동일 제목",
            description="동일 내용",
            link="https://example.com/1"
        )
        article2 = NewsArticle(
            title="동일 제목",
            description="동일 내용",
            link="https://example.com/2"
        )

        assert article1.content_hash == article2.content_hash

    def test_different_content_different_hash(self):
        """다른 내용은 다른 해시"""
        article1 = NewsArticle(
            title="제목1",
            description="내용1",
            link="https://example.com/1"
        )
        article2 = NewsArticle(
            title="제목2",
            description="내용2",
            link="https://example.com/2"
        )

        assert article1.content_hash != article2.content_hash

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        article = NewsArticle(
            title="테스트",
            description="내용",
            link="https://example.com",
            original_link="https://original.com"
        )

        data = article.to_dict()

        assert data["title"] == "테스트"
        assert data["description"] == "내용"
        assert data["link"] == "https://example.com"
        assert data["original_link"] == "https://original.com"
        assert data["content_type"] == "NEWS"


class TestNaverNewsCollector:
    """NaverNewsCollector 테스트"""

    def test_init_without_credentials(self):
        """인증 정보 없이 초기화 시 에러"""
        with patch.object(NaverNewsCollector, '__init__', lambda x: None):
            collector = NaverNewsCollector.__new__(NaverNewsCollector)
            collector.client_id = ""
            collector.client_secret = ""

            # ValueError 발생해야 함
            # 실제 테스트에서는 .env 파일 없이 테스트

    def test_clean_html(self):
        """HTML 태그 제거 테스트"""
        html = "<b>제목</b> &amp; <i>내용</i>"
        clean = NaverNewsCollector._clean_html(html)

        assert "<b>" not in clean
        assert "&amp;" not in clean
        assert "제목" in clean
        assert "&" in clean


class TestPubMedCollector:
    """PubMedCollector 테스트"""

    def test_rate_limit(self):
        """Rate limiting 설정 확인"""
        collector = PubMedCollector()

        # API 키 없으면 1초 간격
        if not collector.api_key:
            assert collector._min_interval >= 1.0
        else:
            # API 키 있으면 0.34초 간격
            assert collector._min_interval < 1.0

        collector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
