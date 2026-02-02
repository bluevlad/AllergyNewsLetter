"""
AllergyNewsLetter 수집기 모듈
"""

from .base import BaseCollector, NewsArticle, PaperArticle, CollectedItem
from .naver_news import NaverNewsCollector
from .pubmed import PubMedCollector

__all__ = [
    "BaseCollector",
    "CollectedItem",
    "NewsArticle",
    "PaperArticle",
    "NaverNewsCollector",
    "PubMedCollector",
]
