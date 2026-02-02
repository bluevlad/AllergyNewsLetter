"""
알러지 콘텐츠 카테고리 분류 모듈
"""

import logging
import re
from typing import Optional

from ..config import settings
from ..database.models import AllergyCategory

logger = logging.getLogger(__name__)


# 알러지 카테고리별 키워드 매핑
ALLERGY_CATEGORY_KEYWORDS = {
    AllergyCategory.CLINICAL: [
        # 치료 관련
        "치료", "치료제", "신약", "항히스타민", "에피네프린", "면역치료",
        "면역요법", "설하면역", "경구면역", "탈감작", "처방", "투약",
        "가이드라인", "프로토콜", "요법", "증상 완화", "응급처치",
        "아나필락시스 치료", "에피펜", "주사", "약물",
        # 영문
        "treatment", "therapy", "immunotherapy", "desensitization",
        "oral immunotherapy", "sublingual", "epinephrine", "antihistamine"
    ],
    AllergyCategory.RESEARCH: [
        # 연구/학술
        "연구", "논문", "학회", "발표", "메커니즘", "임상시험", "임상연구",
        "IgE", "면역글로불린", "항체", "바이오마커", "유전자", "유전적",
        "병태생리", "분자", "세포", "사이토카인", "T세포", "B세포",
        "알레르기 반응", "과민반응", "면역반응",
        # 영문
        "research", "study", "trial", "mechanism", "biomarker",
        "genetic", "molecular", "immunoglobulin", "cytokine"
    ],
    AllergyCategory.LIFESTYLE: [
        # 생활/관리
        "식단", "관리", "예방", "생활", "환경", "대체식품", "대체",
        "저알레르기", "알레르기 프리", "무알레르겐", "라벨", "표시",
        "주의사항", "피해야", "섭취", "식이", "영양", "레시피",
        "세탁", "청소", "공기청정", "미세먼지", "꽃가루",
        "아토피 관리", "보습", "스킨케어", "생활습관",
        # 영문
        "diet", "management", "prevention", "lifestyle", "avoidance",
        "allergen-free", "label", "nutrition"
    ],
    AllergyCategory.MARKET: [
        # 산업/시장
        "시장", "제약사", "투자", "매출", "점유율", "성장",
        "파이프라인", "개발", "출시", "특허", "라이선스",
        "인수", "합병", "M&A", "IPO", "펀딩", "스타트업",
        "진단키트", "검사키트", "알레르기 검사 시장",
        # 영문
        "market", "investment", "pharmaceutical", "pipeline", "launch"
    ],
    AllergyCategory.REGULATION: [
        # 규제/정책
        "식약처", "FDA", "승인", "허가", "인허가", "규제",
        "정책", "법", "보험", "급여", "건강보험", "의료보험",
        "안전", "리콜", "경고", "주의", "가이드라인 발표",
        "식품안전", "표시제", "알레르기 표시",
        # 영문
        "approval", "regulation", "policy", "FDA approved", "MFDS"
    ],
}


class AllergyClassifier:
    """알러지 콘텐츠 분류기"""

    CLASSIFY_PROMPT = """다음 콘텐츠를 아래 카테고리 중 하나로 분류해주세요.

카테고리:
1. 임상/치료 - 신약, 치료법, 면역치료, 가이드라인 관련
2. 연구/학술 - 논문, 연구 결과, 학회 발표, 메커니즘 관련
3. 생활/관리 - 식단, 환경 관리, 예방법, 생활 팁 관련
4. 산업/시장 - 제약사 동향, 시장 분석, 투자 관련
5. 규제/정책 - 식약처, FDA 승인, 정책 변화 관련
6. 기타 - 위 카테고리에 해당하지 않는 경우

제목: {title}
내용: {content}

카테고리 번호만 응답해주세요 (1-6):"""

    CATEGORY_MAP = {
        "1": AllergyCategory.CLINICAL,
        "2": AllergyCategory.RESEARCH,
        "3": AllergyCategory.LIFESTYLE,
        "4": AllergyCategory.MARKET,
        "5": AllergyCategory.REGULATION,
        "6": AllergyCategory.OTHER,
    }

    def __init__(self, use_ollama: bool = True):
        self.use_ollama = use_ollama
        self._client = None
        self._available = False

        if use_ollama:
            try:
                import ollama
                self._client = ollama.Client(host=settings.ollama_host)
                self._available = self._check_availability()
            except Exception as e:
                logger.warning(f"Ollama 초기화 실패: {e}")

    def _check_availability(self) -> bool:
        """Ollama 사용 가능 여부 확인"""
        try:
            models = self._client.list()
            return len(models.get('models', [])) > 0
        except Exception:
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    def classify(self, title: str, content: str) -> AllergyCategory:
        """
        콘텐츠 카테고리 분류

        Args:
            title: 제목
            content: 본문 또는 설명

        Returns:
            AllergyCategory
        """
        # Ollama AI 분류 시도
        if self._available and self.use_ollama:
            category = self._classify_with_ollama(title, content)
            if category:
                return category

        # 키워드 기반 폴백
        return self._classify_by_keywords(title, content)

    def _classify_with_ollama(self, title: str, content: str) -> Optional[AllergyCategory]:
        """Ollama AI 분류"""
        prompt = self.CLASSIFY_PROMPT.format(title=title, content=content[:500])

        try:
            response = self._client.generate(
                model=settings.ollama_model,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 5}
            )
            result = response.get("response", "").strip()

            match = re.search(r'[1-6]', result)
            if match:
                return self.CATEGORY_MAP.get(match.group(), AllergyCategory.OTHER)

        except Exception as e:
            logger.error(f"Ollama 분류 실패: {e}")

        return None

    def _classify_by_keywords(self, title: str, content: str) -> AllergyCategory:
        """키워드 기반 분류"""
        text = f"{title} {content}".lower()

        scores = {category: 0 for category in AllergyCategory}

        for category, keywords in ALLERGY_CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    scores[category] += 1

        max_category = max(scores, key=scores.get)

        if scores[max_category] == 0:
            return AllergyCategory.OTHER

        return max_category

    def classify_batch(self, items: list[dict]) -> list[AllergyCategory]:
        """여러 콘텐츠 일괄 분류"""
        results = []
        for item in items:
            category = self.classify(
                item.get("title", ""),
                item.get("content", item.get("description", ""))
            )
            results.append(category)
        return results


# 싱글톤
_classifier: Optional[AllergyClassifier] = None


def get_classifier() -> AllergyClassifier:
    global _classifier
    if _classifier is None:
        _classifier = AllergyClassifier()
    return _classifier


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    classifier = AllergyClassifier()
    print(f"Ollama 사용 가능: {classifier.is_available}")

    test_cases = [
        {
            "title": "땅콩 알레르기 경구면역치료, FDA 승인 획득",
            "content": "FDA가 땅콩 알레르기 환자를 위한 경구면역치료제를 승인했다.",
            "expected": "규제/정책"
        },
        {
            "title": "우유 알레르기 아이를 위한 대체 식품 가이드",
            "content": "우유 대신 사용할 수 있는 칼슘 풍부한 대체 식품을 소개한다.",
            "expected": "생활/관리"
        },
        {
            "title": "IgE 매개 식품 알레르기의 새로운 바이오마커 발견",
            "content": "연구팀이 식품 알레르기 진단을 위한 새로운 바이오마커를 발견했다.",
            "expected": "연구/학술"
        },
    ]

    print("\n=== 분류 테스트 ===\n")
    for test in test_cases:
        result = classifier.classify(test["title"], test["content"])
        status = "✓" if result.value == test["expected"] else "✗"
        print(f"{status} {test['title'][:40]}...")
        print(f"   예상: {test['expected']} | 결과: {result.value}")
        print()
