"""
PubMed E-utilities API 클라이언트

PubMed API 문서: https://www.ncbi.nlm.nih.gov/books/NBK25499/

Rate Limits:
- API 키 없음: 3 requests/second
- API 키 있음: 10 requests/second

주요 엔드포인트:
- ESearch: 검색 쿼리 → PMID 목록
- EFetch: PMID → 논문 상세 정보
"""

import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass

import httpx

from ..config import settings
from .base import BaseCollector, PaperArticle

logger = logging.getLogger(__name__)


class PubMedCollector(BaseCollector):
    """PubMed 논문 수집기"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        api_key: str = None,
        email: str = None
    ):
        self.api_key = api_key or settings.pubmed_api_key
        self.email = email or settings.pubmed_email

        # Rate limiting
        self._last_request_time = 0
        self._min_interval = 0.34 if self.api_key else 1.0  # seconds between requests

        self._client = httpx.Client(timeout=30.0)

    def _rate_limit(self):
        """Rate limiting 적용"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _build_params(self, **kwargs) -> dict:
        """공통 파라미터 빌드"""
        params = {
            "db": "pubmed",
            "retmode": "xml",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email

        params.update(kwargs)
        return params

    def search(
        self,
        query: str,
        max_results: int = 20,
        days_back: int = 7
    ) -> List[PaperArticle]:
        """
        PubMed 논문 검색

        Args:
            query: 검색어
            max_results: 최대 결과 수
            days_back: 최근 N일 이내 논문만 검색

        Returns:
            PaperArticle 리스트
        """
        # 1. ESearch로 PMID 목록 조회
        pmids = self._esearch(query, max_results, days_back)

        if not pmids:
            logger.info(f"[{query}] 검색 결과 없음")
            return []

        # 2. EFetch로 상세 정보 조회
        papers = self._efetch(pmids, query)

        logger.info(f"[{query}] {len(papers)}개 논문 수집 완료")
        return papers

    def _esearch(
        self,
        query: str,
        max_results: int,
        days_back: int
    ) -> List[str]:
        """ESearch API - PMID 목록 조회"""
        self._rate_limit()

        # 날짜 필터 추가 (mindate/maxdate 파라미터 사용)
        today = datetime.now()
        min_date = (today - timedelta(days=days_back)).strftime("%Y/%m/%d")
        max_date = today.strftime("%Y/%m/%d")

        params = self._build_params(
            term=query,
            retmax=max_results,
            sort="pub_date",
            usehistory="n",
            datetype="pdat",
            mindate=min_date,
            maxdate=max_date
        )

        try:
            response = self._client.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params=params
            )
            response.raise_for_status()

            # XML 파싱
            root = ET.fromstring(response.text)
            pmids = [id_elem.text for id_elem in root.findall(".//Id")]

            logger.debug(f"ESearch 결과: {len(pmids)}개 PMID")
            return pmids

        except Exception as e:
            logger.error(f"ESearch 실패: {e}")
            return []

    def _efetch(self, pmids: List[str], keyword: str) -> List[PaperArticle]:
        """EFetch API - 논문 상세 정보 조회"""
        if not pmids:
            return []

        self._rate_limit()

        params = self._build_params(
            id=",".join(pmids),
            rettype="abstract"
        )

        try:
            response = self._client.get(
                f"{self.BASE_URL}/efetch.fcgi",
                params=params
            )
            response.raise_for_status()

            return self._parse_pubmed_xml(response.text, keyword)

        except Exception as e:
            logger.error(f"EFetch 실패: {e}")
            return []

    def _parse_pubmed_xml(self, xml_text: str, keyword: str) -> List[PaperArticle]:
        """PubMed XML 파싱"""
        papers = []

        try:
            root = ET.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                paper = self._parse_article(article, keyword)
                if paper:
                    papers.append(paper)

        except ET.ParseError as e:
            logger.error(f"XML 파싱 오류: {e}")

        return papers

    def _parse_article(self, article_elem, keyword: str) -> Optional[PaperArticle]:
        """개별 논문 파싱"""
        try:
            medline = article_elem.find(".//MedlineCitation")
            if medline is None:
                return None

            pmid_elem = medline.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""

            article = medline.find(".//Article")
            if article is None:
                return None

            # 제목
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""
            if not title:
                return None

            # 초록
            abstract_elem = article.find(".//Abstract/AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else ""

            # 저널
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else ""

            # 저자 목록
            authors = []
            for author in article.findall(".//Author"):
                lastname = author.find("LastName")
                forename = author.find("ForeName")
                if lastname is not None:
                    name = lastname.text
                    if forename is not None:
                        name = f"{lastname.text} {forename.text}"
                    authors.append(name)

            # 발행일
            pub_date = self._parse_pub_date(article)

            # DOI
            doi = ""
            for article_id in article_elem.findall(".//ArticleIdList/ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text
                    break

            # 링크 생성
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            return PaperArticle(
                title=title,
                description=abstract[:500] if abstract else "",
                link=link,
                pub_date=pub_date,
                source=journal,
                keyword=keyword,
                pmid=pmid,
                doi=doi,
                authors=authors[:5],  # 최대 5명
                journal=journal,
                abstract=abstract,
            )

        except Exception as e:
            logger.error(f"논문 파싱 실패: {e}")
            return None

    def _parse_pub_date(self, article_elem) -> Optional[datetime]:
        """발행일 파싱"""
        try:
            pub_date = article_elem.find(".//PubDate")
            if pub_date is None:
                return None

            year = pub_date.find("Year")
            month = pub_date.find("Month")
            day = pub_date.find("Day")

            if year is None:
                return None

            year_val = int(year.text)
            month_val = 1
            day_val = 1

            if month is not None:
                try:
                    month_val = int(month.text)
                except ValueError:
                    # "Jan", "Feb" 등의 형식
                    month_map = {
                        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
                        "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
                        "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
                    }
                    month_val = month_map.get(month.text[:3], 1)

            if day is not None:
                try:
                    day_val = int(day.text)
                except ValueError:
                    pass

            return datetime(year_val, month_val, day_val)

        except Exception:
            return None

    def collect_by_keywords(
        self,
        keywords: List[str],
        max_per_keyword: int = 20,
        days_back: int = 7
    ) -> List[PaperArticle]:
        """여러 키워드로 논문 수집"""
        all_papers = []
        seen_pmids = set()

        for keyword in keywords:
            papers = self.search(keyword, max_results=max_per_keyword, days_back=days_back)

            for paper in papers:
                if paper.pmid not in seen_pmids:
                    seen_pmids.add(paper.pmid)
                    all_papers.append(paper)

        logger.info(f"총 {len(all_papers)}개 고유 논문 수집 (키워드 {len(keywords)}개)")
        return all_papers

    def close(self):
        """HTTP 클라이언트 종료"""
        self._client.close()


# 알러지 관련 PubMed 검색 키워드
DEFAULT_PUBMED_KEYWORDS = [
    "food allergy",
    "allergen immunotherapy",
    "anaphylaxis",
    "atopic dermatitis",
    "IgE mediated",
    "peanut allergy",
    "oral immunotherapy",
]


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    with PubMedCollector() as collector:
        papers = collector.search("food allergy", max_results=5, days_back=30)

        print(f"\n=== 검색 결과: {len(papers)}건 ===\n")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper.title[:80]}...")
            print(f"   - PMID: {paper.pmid}")
            print(f"   - 저널: {paper.journal}")
            print(f"   - 저자: {', '.join(paper.authors[:3])}")
            print(f"   - 날짜: {paper.pub_date}")
            print()
