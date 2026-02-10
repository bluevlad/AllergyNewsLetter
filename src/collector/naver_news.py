"""
네이버 뉴스 검색 API 클라이언트
"""

import logging
import re
from datetime import datetime
from typing import Optional, List

import httpx

from ..config import settings
from .base import BaseCollector, NewsArticle

logger = logging.getLogger(__name__)


class NaverNewsCollector(BaseCollector):
    """네이버 뉴스 검색 API 클라이언트"""

    BASE_URL = "https://openapi.naver.com/v1/search/news.json"

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None
    ):
        self.client_id = client_id or settings.naver_client_id
        self.client_secret = client_secret or settings.naver_client_secret

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "네이버 API 인증 정보가 필요합니다. "
                ".env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정하세요."
            )

        self._client = httpx.Client(
            headers={
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
            },
            timeout=30.0
        )

    def search(
        self,
        query: str,
        max_results: int = 100,
        start: int = 1,
        sort: str = "date"
    ) -> List[NewsArticle]:
        """
        네이버 뉴스 검색

        Args:
            query: 검색어
            max_results: 검색 결과 수 (최대 100)
            start: 검색 시작 위치
            sort: 정렬 (date: 날짜순, sim: 정확도순)

        Returns:
            NewsArticle 리스트
        """
        params = {
            "query": query,
            "display": min(max_results, 100),
            "start": start,
            "sort": sort,
        }

        try:
            response = self._client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            articles = []
            for item in data.get("items", []):
                article = self._parse_item(item, query)
                if article:
                    articles.append(article)

            logger.info(f"[{query}] {len(articles)}개 기사 수집 완료")
            return articles

        except httpx.HTTPStatusError as e:
            logger.error(f"API 요청 실패: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"뉴스 검색 중 오류: {e}")
            return []

    def _parse_item(self, item: dict, keyword: str) -> Optional[NewsArticle]:
        """API 응답 파싱"""
        try:
            pub_date = None
            if item.get("pubDate"):
                try:
                    pub_date = datetime.strptime(
                        item["pubDate"],
                        "%a, %d %b %Y %H:%M:%S %z"
                    )
                except ValueError:
                    pass

            source = self._extract_source(item.get("originallink", ""))

            return NewsArticle(
                title=self._clean_html(item.get("title", "")),
                description=self._clean_html(item.get("description", "")),
                link=item.get("link", ""),
                original_link=item.get("originallink", ""),
                pub_date=pub_date,
                source=source,
                keyword=keyword,
            )
        except Exception as e:
            logger.error(f"파싱 실패: {e}")
            return None

    @staticmethod
    def _clean_html(text: str) -> str:
        """HTML 태그 제거"""
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = clean.replace("&quot;", '"')
        clean = clean.replace("&amp;", "&")
        clean = clean.replace("&lt;", "<")
        clean = clean.replace("&gt;", ">")
        clean = clean.replace("&apos;", "'")
        return clean.strip()

    def _extract_source(self, url: str) -> str:
        """URL에서 언론사 추출"""
        if not url:
            return ""

        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc

            source_map = {
                "chosun.com": "조선일보",
                "donga.com": "동아일보",
                "joongang.co.kr": "중앙일보",
                "hani.co.kr": "한겨레",
                "khan.co.kr": "경향신문",
                "mk.co.kr": "매일경제",
                "hankyung.com": "한국경제",
                "yna.co.kr": "연합뉴스",
                "news1.kr": "뉴스1",
                "mt.co.kr": "머니투데이",
                "edaily.co.kr": "이데일리",
                "bosa.co.kr": "약사공론",
                "dailypharm.com": "데일리팜",
                "medipana.com": "메디파나뉴스",
                "medigatenews.com": "메디게이트뉴스",
                "health.chosun.com": "헬스조선",
                "hidoc.co.kr": "하이닥",
            }

            for key, value in source_map.items():
                if key in domain:
                    return value

            return domain
        except Exception:
            return ""

    def collect_by_keywords(
        self,
        keywords: List[str],
        max_per_keyword: int = 30
    ) -> List[NewsArticle]:
        """여러 키워드로 뉴스 수집"""
        all_articles = []
        seen_hashes = set()

        for keyword in keywords:
            articles = self.search(keyword, max_results=max_per_keyword)

            for article in articles:
                if article.content_hash not in seen_hashes:
                    seen_hashes.add(article.content_hash)
                    all_articles.append(article)

        logger.info(f"총 {len(all_articles)}개 고유 기사 수집 (키워드 {len(keywords)}개)")
        return all_articles

    def collect_company_news(
        self,
        companies: dict,
        max_per_keyword: int = 10
    ) -> List[NewsArticle]:
        """
        회사별 뉴스 수집

        Args:
            companies: {회사명: {"keywords": [...], "type": "main"|"competitor"}} 형태
            max_per_keyword: 키워드당 최대 기사 수

        Returns:
            company 필드가 태깅된 NewsArticle 리스트
        """
        all_articles = []
        seen_hashes = set()

        for company_name, config in companies.items():
            keywords = config.get("keywords", [])
            company_articles = []

            for keyword in keywords:
                articles = self.search(keyword, max_results=max_per_keyword)

                for article in articles:
                    if article.content_hash not in seen_hashes:
                        seen_hashes.add(article.content_hash)
                        article.company = company_name
                        company_articles.append(article)

            all_articles.extend(company_articles)
            logger.info(f"[업체동향] {company_name}: {len(company_articles)}개 기사 수집")

        logger.info(f"[업체동향] 총 {len(all_articles)}개 기사 수집 완료")
        return all_articles

    def close(self):
        """HTTP 클라이언트 종료"""
        self._client.close()


# 알러지 관련 기본 검색 키워드
DEFAULT_ALLERGY_KEYWORDS = [
    "식품알레르기",
    "알레르기 검사",
    "아나필락시스",
    "면역치료",
    "아토피 치료",
    "알레르기 진단키트",
    "땅콩 알레르기",
    "우유 알레르기",
]


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    try:
        with NaverNewsCollector() as collector:
            articles = collector.search("식품알레르기", max_results=5)

            print(f"\n=== 검색 결과: {len(articles)}건 ===\n")
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article.title}")
                print(f"   - 출처: {article.source}")
                print(f"   - 날짜: {article.pub_date}")
                print()

    except ValueError as e:
        print(f"오류: {e}")
