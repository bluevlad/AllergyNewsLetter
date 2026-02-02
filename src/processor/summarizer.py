"""
알러지 콘텐츠 AI 요약 모듈
"""

import logging
import re
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)


class AllergySummarizer:
    """알러지 콘텐츠 요약기"""

    SUMMARIZE_PROMPT = """다음 알러지 관련 콘텐츠를 3-4문장으로 간결하게 요약해주세요.
핵심 내용과 중요한 수치/데이터를 포함해주세요.
의학 용어는 쉽게 풀어서 설명해주세요.

제목: {title}

내용: {content}

요약:"""

    IMPORTANCE_PROMPT = """다음 알러지 관련 콘텐츠가 알러지 환자/의료진/연구자에게 얼마나 중요한지 0.0~1.0 사이 점수로 평가해주세요.

평가 기준:
- 새로운 치료법/신약 승인: 높은 점수 (0.8~1.0)
- 규제/정책 변화: 높은 점수 (0.7~0.9)
- 중요한 연구 결과: 중간~높은 점수 (0.6~0.8)
- 생활 관리 팁: 중간 점수 (0.4~0.6)
- 일반 뉴스: 낮은 점수 (0.2~0.4)

제목: {title}
내용: {content}

숫자만 응답해주세요 (예: 0.75):"""

    def __init__(self):
        self._client = None
        self._available = False

        try:
            import ollama
            self._client = ollama.Client(host=settings.ollama_host)
            self._available = self._check_availability()
        except Exception as e:
            logger.warning(f"Ollama 초기화 실패: {e}")

    def _check_availability(self) -> bool:
        try:
            models = self._client.list()
            model_names = [m['name'] for m in models.get('models', [])]
            base_model = settings.ollama_model.split(':')[0]

            for name in model_names:
                if base_model in name:
                    logger.info(f"Ollama 모델 '{settings.ollama_model}' 사용 가능")
                    return True

            logger.warning(f"Ollama 모델 '{settings.ollama_model}' 없음")
            return False
        except Exception as e:
            logger.warning(f"Ollama 서버 연결 실패: {e}")
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    def summarize(self, title: str, content: str) -> str:
        """
        콘텐츠 요약 생성

        Args:
            title: 제목
            content: 본문

        Returns:
            요약 텍스트
        """
        if not self._available:
            return self._fallback_summary(title, content)

        prompt = self.SUMMARIZE_PROMPT.format(title=title, content=content[:1000])

        try:
            response = self._client.generate(
                model=settings.ollama_model,
                prompt=prompt,
                options={"temperature": 0.3, "num_predict": 200}
            )
            summary = response.get("response", "").strip()
            return summary if summary else self._fallback_summary(title, content)

        except Exception as e:
            logger.error(f"요약 생성 실패: {e}")
            return self._fallback_summary(title, content)

    def score_importance(self, title: str, content: str) -> float:
        """
        중요도 점수 산정

        Args:
            title: 제목
            content: 본문

        Returns:
            0.0 ~ 1.0 점수
        """
        if not self._available:
            return self._fallback_importance(title, content)

        prompt = self.IMPORTANCE_PROMPT.format(title=title, content=content[:500])

        try:
            response = self._client.generate(
                model=settings.ollama_model,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 10}
            )
            score_text = response.get("response", "").strip()

            match = re.search(r'(\d+\.?\d*)', score_text)
            if match:
                score = float(match.group(1))
                return min(max(score, 0.0), 1.0)

            return self._fallback_importance(title, content)

        except Exception as e:
            logger.error(f"중요도 산정 실패: {e}")
            return self._fallback_importance(title, content)

    def _fallback_summary(self, title: str, content: str) -> str:
        """폴백 요약 (첫 200자)"""
        if content:
            summary = content[:200]
            if len(content) > 200:
                summary += "..."
            return summary
        return title

    def _fallback_importance(self, title: str, content: str) -> float:
        """키워드 기반 중요도 산정"""
        text = f"{title} {content}".lower()

        # 고중요도 키워드
        high_keywords = [
            "fda", "식약처", "승인", "허가", "신약", "치료제",
            "면역치료", "아나필락시스", "응급", "사망", "위험"
        ]
        # 중간 중요도
        medium_keywords = [
            "연구", "임상", "발견", "개발", "논문", "학회",
            "검사", "진단", "바이오마커"
        ]
        # 저중요도
        low_keywords = ["행사", "이벤트", "인터뷰", "기고", "광고"]

        score = 0.5

        for kw in high_keywords:
            if kw in text:
                score += 0.08

        for kw in medium_keywords:
            if kw in text:
                score += 0.04

        for kw in low_keywords:
            if kw in text:
                score -= 0.1

        return min(max(score, 0.0), 1.0)


# 싱글톤
_summarizer: Optional[AllergySummarizer] = None


def get_summarizer() -> AllergySummarizer:
    global _summarizer
    if _summarizer is None:
        _summarizer = AllergySummarizer()
    return _summarizer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    summarizer = AllergySummarizer()
    print(f"Ollama 사용 가능: {summarizer.is_available}")

    test_title = "땅콩 알레르기 환자를 위한 새로운 경구면역치료제 FDA 승인"
    test_content = """
    미국 FDA가 땅콩 알레르기 환자를 위한 새로운 경구면역치료제를 승인했다.
    이 치료제는 4-17세 환자를 대상으로 하며, 땅콩에 대한 심각한 알레르기 반응을
    줄이는 데 효과적인 것으로 임상시험에서 입증되었다.
    치료는 점진적으로 땅콩 단백질 용량을 증가시키는 방식으로 진행된다.
    """

    summary = summarizer.summarize(test_title, test_content)
    print(f"\n요약:\n{summary}")

    score = summarizer.score_importance(test_title, test_content)
    print(f"\n중요도 점수: {score:.2f}")
