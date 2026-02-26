"""
AllergyNewsLetter Report API
NewsLetterPlatform 연동용 REST API
"""

import logging
from datetime import datetime
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import yaml

from ..config import settings
from ..database.repository import get_session, ArticleRepository
from ..database.models import Article, ContentType, AllergyCategory
from ..reporter.generator import (
    NEWS_MEGA_GROUPS, TREND_TARGET_COMPANIES,
    load_trend_target_companies,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["report"])


def _load_company_keywords() -> dict:
    """keywords.yaml에서 회사 키워드 로드"""
    keywords_path = settings.BASE_DIR / "config" / "keywords.yaml"
    try:
        with open(keywords_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("companies", {})
    except Exception as e:
        logger.warning(f"회사 키워드 로드 실패: {e}")
        return {}

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Bearer 토큰 인증"""
    if not settings.api_secret_token:
        raise HTTPException(status_code=500, detail="API_SECRET_TOKEN not configured")
    if credentials.credentials != settings.api_secret_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


def _serialize_article(article: Article) -> dict:
    """Article 객체를 JSON dict로 직렬화"""
    return {
        "id": article.id,
        "content_type": article.content_type.value if article.content_type else None,
        "title": article.title,
        "description": article.description,
        "link": article.link,
        "original_link": article.original_link,
        "pub_date": article.pub_date.strftime("%Y-%m-%d") if article.pub_date else None,
        "source": article.source,
        "keyword": article.keyword,
        "pmid": article.pmid,
        "doi": article.doi,
        "authors": article.authors,
        "journal": article.journal,
        "abstract": article.abstract,
        "company": article.company,
        "category": article.category.value if article.category else None,
        "summary": article.summary,
        "importance_score": article.importance_score,
    }


def _build_news_groups_serialized(news_by_category: dict) -> list:
    """카테고리별 뉴스를 대분류 그룹으로 묶기 (JSON 직렬화)"""
    groups = []
    for group_def in NEWS_MEGA_GROUPS:
        articles_with_category = []
        for cat in group_def["categories"]:
            for article in news_by_category.get(cat, [])[:5]:
                articles_with_category.append({
                    "article": _serialize_article(article),
                    "category_name": cat.value,
                })

        articles_with_category.sort(
            key=lambda x: x["article"]["importance_score"] or 0,
            reverse=True,
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


def _group_by_company_serialized(
    company_articles: list[Article],
    company_types: dict,
) -> list:
    """업체 동향 기사를 회사별로 그룹화 (JSON 직렬화, AI 요약 없이)"""
    if not TREND_TARGET_COMPANIES:
        load_trend_target_companies()

    company_map = defaultdict(list)
    for article in company_articles:
        if article.company:
            company_map[article.company].append(article)

    result = []

    for company_name in TREND_TARGET_COMPANIES:
        articles = company_map.pop(company_name, [])
        articles.sort(key=lambda a: a.importance_score or 0, reverse=True)
        company_type = company_types.get(company_name, "competitor")

        trend_summary = ""
        if articles and articles[0].summary:
            fallback = articles[0].summary
            if len(fallback) > 50:
                fallback = fallback[:47] + "..."
            trend_summary = fallback
        elif articles:
            trend_summary = f"관련 뉴스 {len(articles)}건 수집됨"

        result.append({
            "name": company_name,
            "type": company_type,
            "articles": [_serialize_article(a) for a in articles[:3]],
            "trend_summary": trend_summary,
        })

    result.sort(key=lambda c: (0 if c["type"] == "main" else 1, -len(c["articles"])))

    for company_name, articles in company_map.items():
        articles.sort(key=lambda a: a.importance_score or 0, reverse=True)
        result.append({
            "name": company_name,
            "type": company_types.get(company_name, "competitor"),
            "articles": [_serialize_article(a) for a in articles[:3]],
            "trend_summary": "",
        })

    return result


@router.get("/report")
async def get_report(token: str = Depends(verify_token)):
    """일일 리포트 데이터 조회 API"""
    report_date = datetime.now()

    companies = _load_company_keywords()
    company_types = {
        name: config.get("type", "competitor")
        for name, config in companies.items()
    }

    try:
        with get_session() as session:
            news = ArticleRepository.get_today_articles(
                session,
                content_type=ContentType.NEWS,
                processed_only=True,
                exclude_company=True,
            )
            company_articles = ArticleRepository.get_today_articles(
                session,
                content_type=ContentType.NEWS,
                processed_only=True,
                company_only=True,
            )
            papers = ArticleRepository.get_today_articles(
                session,
                content_type=ContentType.PAPER,
                processed_only=True,
            )

            # 카테고리별 그룹화
            news_by_category = defaultdict(list)
            for article in news:
                category = article.category or AllergyCategory.OTHER
                news_by_category[category].append(article)

            for category in news_by_category:
                news_by_category[category].sort(
                    key=lambda a: a.importance_score or 0,
                    reverse=True,
                )

            # TOP 5
            top_news_articles = sorted(
                news,
                key=lambda a: a.importance_score or 0,
                reverse=True,
            )[:5]

            # 그룹화
            news_groups = _build_news_groups_serialized(news_by_category)
            company_news = _group_by_company_serialized(company_articles, company_types)

            # 동향 분석 대상 기업 수
            trend_company_count = sum(
                1 for c in company_news
                if c["name"] in TREND_TARGET_COMPANIES and len(c["articles"]) > 0
            )

            stats = {
                "news_count": len(news),
                "paper_count": len(papers),
                "company_count": len(company_articles),
                "total_count": len(news) + len(papers) + len(company_articles),
                "trend_company_count": trend_company_count,
            }

            return {
                "report_date": report_date.isoformat(),
                "top_news": [_serialize_article(a) for a in top_news_articles],
                "company_news": company_news,
                "news_groups": news_groups,
                "papers": [_serialize_article(p) for p in papers[:10]],
                "stats": stats,
                "generated_at": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.exception(f"리포트 API 오류: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
