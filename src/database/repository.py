"""
데이터베이스 저장소 패턴 구현
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import sessionmaker, Session

from .models import (
    Base, Article, Recipient, SendHistory, Category, EmailVerification,
    AllergyCategory, RecipientGroup, ContentType, VerificationType
)


_engine = None
_SessionLocal = None


def init_db(database_url: str = "sqlite:///./data/allergynewsletter.db") -> None:
    """데이터베이스 초기화"""
    global _engine, _SessionLocal

    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    _engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    Base.metadata.create_all(bind=_engine)
    _init_default_categories()


def _init_default_categories() -> None:
    """기본 알러지 카테고리 데이터 삽입"""
    with get_session() as session:
        existing = session.query(Category).count()
        if existing > 0:
            return

        default_categories = [
            Category(
                name=AllergyCategory.CLINICAL.value,
                keywords=json.dumps([
                    "치료", "신약", "임상시험", "치료제", "면역치료",
                    "항히스타민", "에피네프린", "처방", "가이드라인"
                ], ensure_ascii=False),
                description="임상 및 치료 관련",
                priority=1
            ),
            Category(
                name=AllergyCategory.RESEARCH.value,
                keywords=json.dumps([
                    "연구", "논문", "학회", "발표", "메커니즘",
                    "IgE", "면역글로불린", "바이오마커", "유전자"
                ], ensure_ascii=False),
                description="연구 및 학술",
                priority=2
            ),
            Category(
                name=AllergyCategory.LIFESTYLE.value,
                keywords=json.dumps([
                    "식단", "관리", "예방", "생활", "환경",
                    "대체식품", "저알레르기", "아토피 관리"
                ], ensure_ascii=False),
                description="생활 및 관리",
                priority=3
            ),
            Category(
                name=AllergyCategory.MARKET.value,
                keywords=json.dumps([
                    "시장", "제약사", "투자", "매출", "점유율",
                    "신약개발", "파이프라인"
                ], ensure_ascii=False),
                description="산업 및 시장",
                priority=4
            ),
            Category(
                name=AllergyCategory.REGULATION.value,
                keywords=json.dumps([
                    "식약처", "FDA", "승인", "허가", "규제",
                    "정책", "보험", "급여"
                ], ensure_ascii=False),
                description="규제 및 정책",
                priority=5
            ),
            Category(
                name=AllergyCategory.OTHER.value,
                keywords=json.dumps([], ensure_ascii=False),
                description="기타",
                priority=99
            ),
        ]

        for cat in default_categories:
            session.add(cat)
        session.commit()


@contextmanager
def get_session():
    """세션 컨텍스트 매니저"""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class ArticleRepository:
    """기사/논문 저장소"""

    @staticmethod
    def create(session: Session, article_data: dict) -> Article:
        """기사/논문 생성"""
        hash_content = f"{article_data.get('title', '')}{article_data.get('description', '')}"
        content_hash = hashlib.sha256(hash_content.encode()).hexdigest()

        # authors 리스트를 JSON 문자열로 변환
        authors = article_data.get("authors")
        if isinstance(authors, list):
            authors = json.dumps(authors, ensure_ascii=False)

        article = Article(
            content_type=article_data.get("content_type", ContentType.NEWS),
            title=article_data.get("title"),
            description=article_data.get("description"),
            link=article_data.get("link"),
            original_link=article_data.get("original_link"),
            pub_date=article_data.get("pub_date"),
            source=article_data.get("source"),
            keyword=article_data.get("keyword"),
            pmid=article_data.get("pmid"),
            doi=article_data.get("doi"),
            authors=authors,
            journal=article_data.get("journal"),
            abstract=article_data.get("abstract"),
            content_hash=content_hash,
            company=article_data.get("company"),
        )

        session.add(article)
        session.flush()
        return article

    @staticmethod
    def get_by_link(session: Session, link: str) -> Optional[Article]:
        """링크로 조회"""
        return session.query(Article).filter(Article.link == link).first()

    @staticmethod
    def get_by_pmid(session: Session, pmid: str) -> Optional[Article]:
        """PubMed ID로 조회"""
        return session.query(Article).filter(Article.pmid == pmid).first()

    @staticmethod
    def exists_by_link(session: Session, link: str) -> bool:
        """링크 존재 여부 확인"""
        return session.query(Article).filter(Article.link == link).count() > 0

    @staticmethod
    def exists_by_pmid(session: Session, pmid: str) -> bool:
        """PMID 존재 여부 확인"""
        return session.query(Article).filter(Article.pmid == pmid).count() > 0

    @staticmethod
    def get_unprocessed(session: Session, limit: int = 100) -> list[Article]:
        """미처리 기사 조회"""
        return (
            session.query(Article)
            .filter(
                and_(
                    Article.is_processed == False,
                    Article.is_duplicate == False
                )
            )
            .order_by(Article.collected_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_today_articles(
        session: Session,
        content_type: ContentType = None,
        processed_only: bool = True,
        company_only: bool = False,
        exclude_company: bool = False
    ) -> list[Article]:
        """오늘 수집된 기사/논문 조회

        Args:
            company_only: True면 company 필드가 있는 기사만 조회
            exclude_company: True면 company 필드가 없는 기사만 조회
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        query = session.query(Article).filter(
            and_(
                Article.collected_at >= today_start,
                Article.is_duplicate == False
            )
        )

        if content_type:
            query = query.filter(Article.content_type == content_type)

        if processed_only:
            query = query.filter(Article.is_processed == True)

        if company_only:
            query = query.filter(Article.company.isnot(None))
        elif exclude_company:
            query = query.filter(Article.company.is_(None))

        return query.order_by(Article.importance_score.desc()).all()

    @staticmethod
    def get_latest_articles(
        session: Session,
        content_type: ContentType = None,
        processed_only: bool = True,
        company_only: bool = False,
        exclude_company: bool = False
    ) -> list[Article]:
        """가장 최근 수집된 기사/논문 조회 (마지막 수집 일자 기준)"""
        # 가장 최근 수집 일자 조회
        latest_date_query = session.query(
            func.date(Article.collected_at)
        ).filter(
            Article.is_duplicate == False
        )

        if content_type:
            latest_date_query = latest_date_query.filter(Article.content_type == content_type)

        if processed_only:
            latest_date_query = latest_date_query.filter(Article.is_processed == True)

        latest_date = latest_date_query.order_by(Article.collected_at.desc()).first()

        if not latest_date or not latest_date[0]:
            return []

        # 해당 일자의 기사 조회
        query = session.query(Article).filter(
            and_(
                func.date(Article.collected_at) == latest_date[0],
                Article.is_duplicate == False
            )
        )

        if content_type:
            query = query.filter(Article.content_type == content_type)

        if processed_only:
            query = query.filter(Article.is_processed == True)

        if company_only:
            query = query.filter(Article.company.isnot(None))
        elif exclude_company:
            query = query.filter(Article.company.is_(None))

        return query.order_by(Article.importance_score.desc()).all()

    @staticmethod
    def get_recent_hashes(session: Session, days: int = 7) -> list[str]:
        """최근 N일간 해시 목록"""
        since = datetime.utcnow() - timedelta(days=days)
        results = (
            session.query(Article.content_hash)
            .filter(Article.collected_at >= since)
            .all()
        )
        return [r[0] for r in results if r[0]]

    @staticmethod
    def update_analysis(
        session: Session,
        article_id: int,
        category: AllergyCategory,
        summary: str,
        importance_score: float
    ) -> None:
        """AI 분석 결과 업데이트"""
        article = session.query(Article).filter(Article.id == article_id).first()
        if article:
            article.category = category
            article.summary = summary
            article.importance_score = importance_score
            article.is_processed = True
            article.processed_at = datetime.utcnow()

    @staticmethod
    def mark_as_duplicate(session: Session, article_id: int) -> None:
        """중복으로 마킹"""
        article = session.query(Article).filter(Article.id == article_id).first()
        if article:
            article.is_duplicate = True


class RecipientRepository:
    """수신자 저장소"""

    @staticmethod
    def create(session: Session, email: str, name: str, group: RecipientGroup) -> Recipient:
        """수신자 생성"""
        recipient = Recipient(email=email, name=name, group=group)
        session.add(recipient)
        session.flush()
        return recipient

    @staticmethod
    def get_by_email(session: Session, email: str) -> Optional[Recipient]:
        """이메일로 조회"""
        return session.query(Recipient).filter(Recipient.email == email).first()

    @staticmethod
    def get_all_active(session: Session) -> list[Recipient]:
        """모든 활성 수신자 조회"""
        return session.query(Recipient).filter(Recipient.is_active == True).all()


class SendHistoryRepository:
    """발송 이력 저장소"""

    @staticmethod
    def create(
        session: Session,
        recipient_id: int,
        subject: str,
        article_count: int,
        paper_count: int,
        report_date: datetime,
        is_success: bool,
        error_message: str = None
    ) -> SendHistory:
        """발송 이력 생성"""
        history = SendHistory(
            recipient_id=recipient_id,
            subject=subject,
            article_count=article_count,
            paper_count=paper_count,
            report_date=report_date,
            is_success=is_success,
            error_message=error_message
        )
        session.add(history)
        session.flush()
        return history

    @staticmethod
    def already_sent_today(session: Session, recipient_id: int) -> bool:
        """오늘 이미 발송했는지 확인"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        return (
            session.query(SendHistory)
            .filter(
                and_(
                    SendHistory.recipient_id == recipient_id,
                    SendHistory.sent_at >= today_start,
                    SendHistory.is_success == True
                )
            )
            .count() > 0
        )
