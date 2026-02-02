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
        report_date: datetime = None,
        recipient_name: str = None
    ) -> str:
        """
        일일 리포트 HTML 생성

        Args:
            articles: 뉴스 기사 목록
            papers: 논문 목록
            report_date: 리포트 날짜
            recipient_name: 수신자 이름

        Returns:
            HTML 문자열
        """
        if report_date is None:
            report_date = datetime.now()

        if papers is None:
            papers = []

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

        # 논문 카테고리별 그룹화
        papers_by_category = defaultdict(list)
        for paper in papers:
            category = paper.category or AllergyCategory.RESEARCH
            papers_by_category[category].append(paper)

        # 카테고리 순서
        category_order = [
            AllergyCategory.CLINICAL,
            AllergyCategory.RESEARCH,
            AllergyCategory.LIFESTYLE,
            AllergyCategory.MARKET,
            AllergyCategory.REGULATION,
            AllergyCategory.OTHER,
        ]

        # 정렬된 뉴스 카테고리
        sorted_news_categories = []
        for category in category_order:
            if category in news_by_category:
                sorted_news_categories.append({
                    "name": category.value,
                    "articles": news_by_category[category][:5]
                })

        # 통계
        stats = {
            "news_count": len(articles),
            "paper_count": len(papers),
            "total_count": len(articles) + len(papers),
        }

        # 템플릿 렌더링
        try:
            template = self._env.get_template("allergy_briefing.html")
            html = template.render(
                report_date=report_date,
                recipient_name=recipient_name,
                top_news=top_news,
                news_categories=sorted_news_categories,
                papers=papers[:10],
                stats=stats,
                generated_at=datetime.now(),
            )
            return html

        except Exception as e:
            logger.error(f"템플릿 렌더링 실패: {e}")
            return self._generate_fallback_html(articles, papers, report_date, recipient_name)

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
