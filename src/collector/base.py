"""
수집기 공통 인터페이스 정의
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import hashlib


@dataclass
class CollectedItem:
    """수집된 아이템 (뉴스/논문) 기본 클래스"""
    title: str
    description: str
    link: str
    pub_date: Optional[datetime] = None
    source: Optional[str] = None
    keyword: str = ""
    content_hash: str = field(default="", init=False)

    def __post_init__(self):
        """컨텐츠 해시 생성"""
        hash_content = f"{self.title}{self.description}"
        self.content_hash = hashlib.sha256(hash_content.encode()).hexdigest()

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "pub_date": self.pub_date,
            "source": self.source,
            "keyword": self.keyword,
            "content_hash": self.content_hash,
        }


@dataclass
class NewsArticle(CollectedItem):
    """뉴스 기사"""
    original_link: str = ""
    company: Optional[str] = None  # 관련 회사명 (업체 동향용)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["original_link"] = self.original_link
        data["content_type"] = "NEWS"
        if self.company:
            data["company"] = self.company
        return data


@dataclass
class PaperArticle(CollectedItem):
    """논문"""
    pmid: str = ""
    doi: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    abstract: str = ""

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["pmid"] = self.pmid
        data["doi"] = self.doi
        data["authors"] = self.authors
        data["journal"] = self.journal
        data["abstract"] = self.abstract
        data["content_type"] = "PAPER"
        return data


class BaseCollector(ABC):
    """수집기 기본 인터페이스"""

    @abstractmethod
    def search(self, query: str, max_results: int = 50) -> List[CollectedItem]:
        """
        검색 수행

        Args:
            query: 검색어
            max_results: 최대 결과 수

        Returns:
            수집된 아이템 목록
        """
        pass

    @abstractmethod
    def collect_by_keywords(
        self,
        keywords: List[str],
        max_per_keyword: int = 30
    ) -> List[CollectedItem]:
        """
        여러 키워드로 수집

        Args:
            keywords: 검색 키워드 목록
            max_per_keyword: 키워드당 최대 결과 수

        Returns:
            중복 제거된 수집 결과
        """
        pass

    def close(self):
        """리소스 정리"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
