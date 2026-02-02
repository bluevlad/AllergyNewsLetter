"""
AllergyNewsLetter 데이터베이스 모델 정의
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ContentType(PyEnum):
    """콘텐츠 유형"""
    NEWS = "뉴스"
    PAPER = "논문"


class AllergyCategory(PyEnum):
    """알러지 콘텐츠 카테고리"""
    CLINICAL = "임상/치료"         # 신약, 치료법, 가이드라인
    RESEARCH = "연구/학술"         # 논문, 학회, 연구 결과
    LIFESTYLE = "생활/관리"        # 식단, 환경, 예방법
    MARKET = "산업/시장"           # 제약사, 시장 동향
    REGULATION = "규제/정책"       # 식약처, FDA, 정책
    OTHER = "기타"


class RecipientGroup(PyEnum):
    """수신자 그룹"""
    PATIENT = "환자/보호자"
    MEDICAL = "의료진"
    RESEARCHER = "연구자"
    ALL = "전체"


class Article(Base):
    """수집된 뉴스/논문"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 콘텐츠 유형
    content_type = Column(Enum(ContentType), default=ContentType.NEWS)

    # 기본 정보
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content = Column(Text)
    link = Column(String(1000), unique=True, nullable=False)
    original_link = Column(String(1000))

    # 메타데이터
    pub_date = Column(DateTime)
    source = Column(String(100))       # 언론사 또는 저널명
    keyword = Column(String(100))      # 검색 키워드

    # 논문 전용 필드
    pmid = Column(String(20))          # PubMed ID
    doi = Column(String(100))          # DOI
    authors = Column(Text)             # 저자 목록 (JSON)
    journal = Column(String(200))      # 저널명
    abstract = Column(Text)            # 초록

    # AI 분석 결과
    category = Column(Enum(AllergyCategory), default=AllergyCategory.OTHER)
    summary = Column(Text)
    importance_score = Column(Float, default=0.0)

    # 중복 탐지
    content_hash = Column(String(64))
    is_duplicate = Column(Boolean, default=False)

    # 처리 상태
    is_processed = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)

    # 타임스탬프
    collected_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    __table_args__ = (
        Index("idx_article_pub_date", "pub_date"),
        Index("idx_article_category", "category"),
        Index("idx_article_content_type", "content_type"),
        Index("idx_article_keyword", "keyword"),
        Index("idx_article_collected", "collected_at"),
        Index("idx_article_content_hash", "content_hash"),
        Index("idx_article_pmid", "pmid"),
    )

    def __repr__(self):
        return f"<Article(id={self.id}, type={self.content_type.value}, title='{self.title[:30]}...')>"


class Recipient(Base):
    """이메일 수신자"""
    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, autoincrement=True)

    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100))
    group = Column(Enum(RecipientGroup), default=RecipientGroup.ALL)

    # 선호 카테고리 (JSON)
    preferred_categories = Column(Text)

    # 관심 알러젠 (JSON) - 예: ["땅콩", "우유", "계란"]
    allergens_of_interest = Column(Text)

    # 구독 해지 토큰
    unsubscribe_token = Column(String(64), unique=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    send_histories = relationship("SendHistory", back_populates="recipient")

    def __repr__(self):
        return f"<Recipient(email='{self.email}', group='{self.group.value}')>"


class SendHistory(Base):
    """이메일 발송 이력"""
    __tablename__ = "send_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    recipient_id = Column(Integer, ForeignKey("recipients.id"), nullable=False)

    subject = Column(String(500))
    article_count = Column(Integer, default=0)
    paper_count = Column(Integer, default=0)
    report_date = Column(DateTime)

    is_success = Column(Boolean, default=False)
    error_message = Column(Text)

    sent_at = Column(DateTime, default=datetime.utcnow)

    recipient = relationship("Recipient", back_populates="send_histories")

    __table_args__ = (
        Index("idx_send_history_date", "report_date"),
        Index("idx_send_history_recipient", "recipient_id"),
    )

    def __repr__(self):
        return f"<SendHistory(recipient_id={self.recipient_id}, sent_at='{self.sent_at}')>"


class Category(Base):
    """카테고리 분류 규칙"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(50), unique=True, nullable=False)
    keywords = Column(Text)  # 분류 키워드 (JSON)
    description = Column(String(200))
    priority = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Category(name='{self.name}')>"
