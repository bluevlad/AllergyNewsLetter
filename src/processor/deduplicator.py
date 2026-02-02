"""
콘텐츠 중복 탐지 모듈
"""

import logging
import hashlib
from typing import Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DuplicateResult:
    """중복 탐지 결과"""
    is_duplicate: bool
    similarity_score: float
    matched_hash: Optional[str] = None


class ContentDeduplicator:
    """콘텐츠 중복 탐지기"""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self._hash_cache: Set[str] = set()

    def compute_hash(self, title: str, content: str = "") -> str:
        """컨텐츠 해시 계산"""
        text = f"{title}{content}".strip().lower()
        return hashlib.sha256(text.encode()).hexdigest()

    def check_duplicate(
        self,
        title: str,
        content: str,
        existing_hashes: Set[str] = None
    ) -> DuplicateResult:
        """
        중복 여부 확인

        Args:
            title: 제목
            content: 본문
            existing_hashes: 기존 해시 집합

        Returns:
            DuplicateResult
        """
        new_hash = self.compute_hash(title, content)

        # 캐시에서 체크
        if new_hash in self._hash_cache:
            return DuplicateResult(
                is_duplicate=True,
                similarity_score=1.0,
                matched_hash=new_hash
            )

        # 기존 해시에서 체크
        if existing_hashes and new_hash in existing_hashes:
            return DuplicateResult(
                is_duplicate=True,
                similarity_score=1.0,
                matched_hash=new_hash
            )

        # 중복 아님 - 캐시에 추가
        self._hash_cache.add(new_hash)
        return DuplicateResult(is_duplicate=False, similarity_score=0.0)

    def check_duplicate_simple(
        self,
        title: str,
        content: str,
        existing_hashes: Set[str]
    ) -> bool:
        """간단한 해시 기반 중복 체크"""
        new_hash = self.compute_hash(title, content)
        return new_hash in existing_hashes

    def clear_cache(self):
        """캐시 초기화"""
        self._hash_cache.clear()


# 싱글톤
_deduplicator: Optional[ContentDeduplicator] = None


def get_deduplicator() -> ContentDeduplicator:
    global _deduplicator
    if _deduplicator is None:
        _deduplicator = ContentDeduplicator()
    return _deduplicator
