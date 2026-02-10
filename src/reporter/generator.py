"""
HTML 이메일 리포트 생성기
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import settings
from ..database.models import Article, AllergyCategory, ContentType

# 동향 분석 대상 기업 목록 (이 기업들만 동향 분석 섹션에 표시)
TREND_TARGET_COMPANIES = ["수젠텍", "에스디바이오센서", "바디텍메드", "프로테옴텍"]

# 뉴스 대분류 그룹 정의
NEWS_MEGA_GROUPS = [
    {
        "key": "medical_research",
        "title": "의학·연구 소식",
        "icon": "🔬",
        "color": "#1565c0",
        "border_color": "#1565c0",
        "bg_color": "#e3f2fd",
        "categories": [AllergyCategory.CLINICAL, AllergyCategory.RESEARCH],
    },
    {
        "key": "industry_life",
        "title": "산업·생활 소식",
        "icon": "📋",
        "color": "#6a1b9a",
        "border_color": "#6a1b9a",
        "bg_color": "#f3e5f5",
        "categories": [
            AllergyCategory.LIFESTYLE,
            AllergyCategory.MARKET,
            AllergyCategory.REGULATION,
            AllergyCategory.OTHER,
        ],
    },
]

logger = logging.getLogger(__name__)


class ReportGenerator:
    """HTML 이메일 리포트 생성기"""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = settings.BASE_DIR / "templates"

        self.template_dir = Path(template_dir)

        self._env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self._env.filters['format_date'] = self._format_date
        self._env.filters['truncate_text'] = self._truncate_text

    @staticmethod
    def _format_date(dt: datetime, fmt: str = "%Y-%m-%d") -> str:
        if dt is None:
            return ""
        if isinstance(dt, str):
            return dt
        return dt.strftime(fmt)

    @staticmethod
    def _truncate_text(text: str, length: int = 150) -> str:
        if not text:
            return ""
        if len(text) <= length:
            return text
        return text[:length] + "..."

    def generate_daily_report(
        self,
        articles: List[Article],
        papers: List[Article] = None,
        company_articles: List[Article] = None,
        report_date: datetime = None,
        recipient_name: str = None,
        company_types: dict = None
    ) -> str:
        """
        일일 리포트 HTML 생성

        Args:
            articles: 뉴스 기사 목록 (업체동향 제외)
            papers: 논문 목록
            company_articles: 업체 동향 기사 목록
            report_date: 리포트 날짜
            recipient_name: 수신자 이름
            company_types: 회사별 유형 (main/competitor)

        Returns:
            HTML 문자열
        """
        if report_date is None:
            report_date = datetime.now()

        if papers is None:
            papers = []

        if company_articles is None:
            company_articles = []

        if company_types is None:
            company_types = {}

        # 뉴스 카테고리별 그룹화
        news_by_category = defaultdict(list)
        for article in articles:
            category = article.category or AllergyCategory.OTHER
            news_by_category[category].append(article)

        # 중요도 순 정렬
        for category in news_by_category:
            news_by_category[category].sort(
                key=lambda a: a.importance_score or 0,
                reverse=True
            )

        # TOP 5 뉴스
        top_news = sorted(
            articles,
            key=lambda a: a.importance_score or 0,
            reverse=True
        )[:5]

        # 업체동향 회사별 그룹화 (동향 분석 포함)
        company_news = self._group_by_company(company_articles, company_types)

        # 논문 카테고리별 그룹화
        papers_by_category = defaultdict(list)
        for paper in papers:
            category = paper.category or AllergyCategory.RESEARCH
            papers_by_category[category].append(paper)

        # 대분류 그룹화
        news_groups = self._build_news_groups(news_by_category)

        # 동향 분석 대상 기업 중 뉴스가 있는 기업 수
        trend_company_count = sum(
            1 for c in company_news
            if c["name"] in TREND_TARGET_COMPANIES and len(c["articles"]) > 0
        )

        # 통계
        stats = {
            "news_count": len(articles),
            "paper_count": len(papers),
            "company_count": len(company_articles),
            "total_count": len(articles) + len(papers) + len(company_articles),
            "trend_company_count": trend_company_count,
        }

        # 템플릿 렌더링
        try:
            template = self._env.get_template("allergy_briefing.html")
            html = template.render(
                report_date=report_date,
                recipient_name=recipient_name,
                top_news=top_news,
                company_news=company_news,
                news_groups=news_groups,
                papers=papers[:10],
                stats=stats,
                generated_at=datetime.now(),
            )
            return html

        except Exception as e:
            logger.error(f"템플릿 렌더링 실패: {e}")
            return self._generate_fallback_html(articles, papers, report_date, recipient_name)

    @staticmethod
    def _build_news_groups(news_by_category: dict) -> list:
        """카테고리별 뉴스를 대분류 그룹으로 묶기"""
        groups = []
        for group_def in NEWS_MEGA_GROUPS:
            articles_with_category = []
            for cat in group_def["categories"]:
                for article in news_by_category.get(cat, [])[:5]:
                    articles_with_category.append({
                        "article": article,
                        "category_name": cat.value,
                    })

            # 중요도 순 정렬
            articles_with_category.sort(
                key=lambda x: x["article"].importance_score or 0,
                reverse=True
            )

            if articles_with_category:
                groups.append({
                    "title": group_def["title"],
                    "icon": group_def["icon"],
                    "color": group_def["color"],
                    "border_color": group_def["border_color"],
                    "bg_color": group_def["bg_color"],
                    "entries": articles_with_category[:8],
                    "total_count": len(articles_with_category),
                })

        return groups

    def _group_by_company(
        self,
        company_articles: List[Article],
        company_types: dict = None
    ) -> list:
        """업체 동향 기사를 회사별로 그룹화 (동향 분석 포함)"""
        if company_types is None:
            company_types = {}

        company_map = defaultdict(list)
        for article in company_articles:
            if article.company:
                company_map[article.company].append(article)

        result = []

        # 동향 분석 대상 기업 처리 (뉴스가 없어도 포함)
        for company_name in TREND_TARGET_COMPANIES:
            articles = company_map.pop(company_name, [])
            articles.sort(key=lambda a: a.importance_score or 0, reverse=True)
            company_type = company_types.get(company_name, "competitor")

            trend_summary = ""
            if articles:
                trend_summary = self._generate_trend_summary(company_name, articles)

            result.append({
                "name": company_name,
                "type": company_type,
                "articles": articles[:3],
                "trend_summary": trend_summary,
            })

        # main 기업이 맨 위, 이후 기사 수 내림차순 정렬
        result.sort(key=lambda c: (0 if c["type"] == "main" else 1, -len(c["articles"])))

        # 동향 분석 대상이 아닌 나머지 기업 (기존 방식으로 추가)
        for company_name, articles in company_map.items():
            articles.sort(key=lambda a: a.importance_score or 0, reverse=True)
            result.append({
                "name": company_name,
                "type": company_types.get(company_name, "competitor"),
                "articles": articles[:3],
                "trend_summary": "",
            })

        return result

    def _generate_trend_summary(self, company_name: str, articles: List[Article]) -> str:
        """기업의 뉴스를 기반으로 동향 한줄 요약 생성"""
        try:
            import ollama
            client = ollama.Client(host=settings.ollama_host)

            # 모델 가용성 확인
            models = client.list()
            model_names = [m['name'] for m in models.get('models', [])]
            base_model = settings.ollama_model.split(':')[0]
            model_available = any(base_model in name for name in model_names)

            if model_available:
                titles = "\n".join(f"- {a.title}" for a in articles[:5])
                prompt = (
                    f"다음은 '{company_name}'과 관련된 최근 뉴스 제목들입니다.\n"
                    f"{titles}\n\n"
                    f"이 뉴스들을 종합하여 '{company_name}'의 최근 동향을 한 문장(30자 이내)으로 요약해주세요.\n"
                    f"예시: '신규 진단키트 출시로 시장 확대 중'\n"
                    f"요약:"
                )

                response = client.generate(
                    model=settings.ollama_model,
                    prompt=prompt,
                    options={"temperature": 0.3, "num_predict": 50}
                )
                summary = response.get("response", "").strip()
                # 첫 줄만 사용, 따옴표 제거
                summary = summary.split('\n')[0].strip().strip("'\"")
                if summary:
                    return summary

        except Exception as e:
            logger.debug(f"동향 요약 AI 생성 실패 ({company_name}): {e}")

        # Fallback: 최상위 기사의 summary 또는 기사 수 기반 문구
        if articles and articles[0].summary:
            fallback = articles[0].summary
            if len(fallback) > 50:
                fallback = fallback[:47] + "..."
            return fallback

        return f"관련 뉴스 {len(articles)}건 수집됨"

    def _generate_fallback_html(
        self,
        articles: List[Article],
        papers: List[Article],
        report_date: datetime,
        recipient_name: str = None
    ) -> str:
        """폴백 HTML 생성"""
        date_str = report_date.strftime("%Y년 %m월 %d일")

        html_parts = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'></head>",
            "<body style='font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;'>",
            f"<h1 style='color: #2e7d32;'>AllergyNewsLetter</h1>",
            f"<h2>알러지 뉴스 브리핑 - {date_str}</h2>",
        ]

        if recipient_name:
            html_parts.append(f"<p>{recipient_name}님께,</p>")

        html_parts.append(f"<p>오늘의 알러지 관련 뉴스 {len(articles)}건, 논문 {len(papers)}건을 안내드립니다.</p>")
        html_parts.append("<hr>")

        # 뉴스 섹션
        if articles:
            html_parts.append("<h2>📰 뉴스</h2>")
            for i, article in enumerate(articles[:10], 1):
                score = article.importance_score or 0
                category = article.category.value if article.category else "기타"

                html_parts.append(f"""
                <div style='margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; border-left: 4px solid #2e7d32;'>
                    <h3 style='margin: 0 0 10px 0;'>
                        <a href='{article.link}' style='color: #1565c0; text-decoration: none;'>{article.title}</a>
                    </h3>
                    <p style='color: #666; font-size: 13px; margin: 5px 0;'>
                        [{category}] 중요도: {score:.0%} | {article.source or '출처 미상'}
                    </p>
                    <p style='margin: 10px 0; font-size: 14px;'>{article.summary or article.description or ''}</p>
                </div>
                """)

        # 논문 섹션
        if papers:
            html_parts.append("<h2>📚 최신 논문</h2>")
            for paper in papers[:5]:
                html_parts.append(f"""
                <div style='margin-bottom: 15px; padding: 12px; background: #f5f5f5; border-radius: 6px;'>
                    <h4 style='margin: 0 0 8px 0;'>
                        <a href='{paper.link}' style='color: #1565c0; text-decoration: none;'>{paper.title}</a>
                    </h4>
                    <p style='color: #666; font-size: 12px; margin: 5px 0;'>
                        {paper.journal or ''} | PMID: {paper.pmid or 'N/A'}
                    </p>
                </div>
                """)

        html_parts.append("<hr>")
        html_parts.append("<p style='color: #999; font-size: 12px;'>")
        html_parts.append("이 메일은 AllergyNewsLetter 시스템에서 자동 생성되었습니다.")
        html_parts.append("</p>")
        html_parts.append("</body></html>")

        return "\n".join(html_parts)


# 싱글톤
_generator: Optional[ReportGenerator] = None


def get_generator() -> ReportGenerator:
    global _generator
    if _generator is None:
        _generator = ReportGenerator()
    return _generator
