"""
알러지 분류기 테스트
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.models import AllergyCategory
from src.processor.classifier import AllergyClassifier, ALLERGY_CATEGORY_KEYWORDS


class TestAllergyClassifier:
    """AllergyClassifier 테스트"""

    @pytest.fixture
    def classifier(self):
        """분류기 인스턴스 (Ollama 비활성화)"""
        return AllergyClassifier(use_ollama=False)

    def test_classify_clinical(self, classifier):
        """임상/치료 카테고리 분류 테스트"""
        title = "땅콩 알레르기 경구면역치료제 FDA 승인"
        content = "새로운 면역치료제가 아나필락시스 위험을 줄이는 것으로 확인되었다."

        result = classifier.classify(title, content)
        assert result in [AllergyCategory.CLINICAL, AllergyCategory.REGULATION]

    def test_classify_research(self, classifier):
        """연구/학술 카테고리 분류 테스트"""
        title = "IgE 매개 식품알레르기의 새로운 바이오마커 발견"
        content = "연구팀이 임상시험을 통해 새로운 바이오마커를 발견했다."

        result = classifier.classify(title, content)
        assert result == AllergyCategory.RESEARCH

    def test_classify_lifestyle(self, classifier):
        """생활/관리 카테고리 분류 테스트"""
        title = "우유 알레르기 아이를 위한 대체 식품 가이드"
        content = "저알레르기 식단과 대체 식품을 통한 영양 관리 방법"

        result = classifier.classify(title, content)
        assert result == AllergyCategory.LIFESTYLE

    def test_classify_market(self, classifier):
        """산업/시장 카테고리 분류 테스트"""
        title = "알레르기 진단키트 시장 연간 15% 성장 전망"
        content = "제약사들의 투자 확대로 시장 규모가 급성장하고 있다."

        result = classifier.classify(title, content)
        assert result == AllergyCategory.MARKET

    def test_classify_regulation(self, classifier):
        """규제/정책 카테고리 분류 테스트"""
        title = "식약처, 알레르기 표시제 개정안 발표"
        content = "식품안전 정책 강화를 위해 알레르기 표시 규제를 확대한다."

        result = classifier.classify(title, content)
        assert result == AllergyCategory.REGULATION

    def test_classify_other(self, classifier):
        """기타 카테고리 분류 테스트"""
        title = "오늘의 날씨"
        content = "전국적으로 맑은 날씨가 예상됩니다."

        result = classifier.classify(title, content)
        assert result == AllergyCategory.OTHER

    def test_keywords_exist(self):
        """카테고리별 키워드 존재 확인"""
        for category in AllergyCategory:
            if category != AllergyCategory.OTHER:
                assert category in ALLERGY_CATEGORY_KEYWORDS
                assert len(ALLERGY_CATEGORY_KEYWORDS[category]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
