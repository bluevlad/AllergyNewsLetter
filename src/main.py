"""
AllergyNewsLetter 메인 실행 파일

알러지 뉴스/논문 브리핑 자동화 서비스
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.database import (
    init_db, get_session,
    ArticleRepository, RecipientRepository, SendHistoryRepository,
    ContentType, AllergyCategory
)
from src.collector import NaverNewsCollector, PubMedCollector
from src.processor import get_classifier, get_summarizer, get_deduplicator
from src.reporter import get_generator
from src.mailer import get_sender

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            settings.BASE_DIR / "logs" / "allergynewsletter.log",
            encoding="utf-8"
        ),
    ],
)

logger = logging.getLogger(__name__)


# 기본 검색 키워드
DEFAULT_NEWS_KEYWORDS = [
    "식품알레르기",
    "알레르기 검사",
    "아나필락시스",
    "면역치료",
    "아토피 치료",
    "알레르기 진단",
    "땅콩 알레르기",
    "우유 알레르기",
]

DEFAULT_PUBMED_KEYWORDS = [
    "food allergy",
    "allergen immunotherapy",
    "anaphylaxis",
    "atopic dermatitis",
    "peanut allergy",
]


def run_crawl_job():
    """크롤링 작업 실행"""
    logger.info("=" * 50)
    logger.info("AllergyNewsLetter 크롤링 작업 시작")
    logger.info("=" * 50)

    try:
        # 1. 뉴스 수집
        logger.info("[1/3] 네이버 뉴스 수집 시작...")
        news_count = collect_news()
        logger.info(f"[1/3] 뉴스 수집 완료: {news_count}건")

        # 2. 논문 수집
        logger.info("[2/3] PubMed 논문 수집 시작...")
        paper_count = collect_papers()
        logger.info(f"[2/3] 논문 수집 완료: {paper_count}건")

        # 3. AI 분석
        logger.info("[3/3] AI 분석 시작...")
        processed_count = process_articles()
        logger.info(f"[3/3] 분석 완료: {processed_count}건")

        logger.info("=" * 50)
        logger.info("크롤링 작업 완료")
        logger.info("=" * 50)

    except Exception as e:
        logger.exception(f"크롤링 작업 중 오류 발생: {e}")


def run_send_job():
    """뉴스레터 발송 작업 실행"""
    logger.info("=" * 50)
    logger.info("AllergyNewsLetter 뉴스레터 발송 시작")
    logger.info("=" * 50)

    try:
        send_count = generate_and_send_reports()
        logger.info(f"발송 완료: {send_count}건")

        logger.info("=" * 50)
        logger.info("뉴스레터 발송 완료")
        logger.info("=" * 50)

    except Exception as e:
        logger.exception(f"뉴스레터 발송 중 오류 발생: {e}")


def run_daily_job():
    """일일 작업 전체 실행"""
    logger.info("=" * 50)
    logger.info("AllergyNewsLetter 일일 작업 시작")
    logger.info("=" * 50)

    try:
        # 1. 뉴스 수집
        logger.info("[1/4] 네이버 뉴스 수집...")
        news_count = collect_news()
        logger.info(f"[1/4] 뉴스 수집 완료: {news_count}건")

        # 2. 논문 수집
        logger.info("[2/4] PubMed 논문 수집...")
        paper_count = collect_papers()
        logger.info(f"[2/4] 논문 수집 완료: {paper_count}건")

        if news_count == 0 and paper_count == 0:
            logger.warning("수집된 콘텐츠가 없습니다.")
            return

        # 3. AI 분석
        logger.info("[3/4] AI 분석...")
        processed_count = process_articles()
        logger.info(f"[3/4] 분석 완료: {processed_count}건")

        # 4. 리포트 발송
        logger.info("[4/4] 리포트 발송...")
        send_count = generate_and_send_reports()
        logger.info(f"[4/4] 발송 완료: {send_count}건")

        logger.info("=" * 50)
        logger.info("일일 작업 완료")
        logger.info("=" * 50)

    except Exception as e:
        logger.exception(f"일일 작업 중 오류 발생: {e}")


def collect_news() -> int:
    """뉴스 수집"""
    try:
        collector = NaverNewsCollector()
        deduplicator = get_deduplicator()

        with get_session() as session:
            existing_hashes = set(ArticleRepository.get_recent_hashes(session, days=7))
            new_count = 0

            articles = collector.collect_by_keywords(
                DEFAULT_NEWS_KEYWORDS,
                max_per_keyword=30
            )

            for article in articles:
                # 중복 체크
                if article.content_hash in existing_hashes:
                    continue

                if ArticleRepository.exists_by_link(session, article.link):
                    continue

                # 저장
                article_data = article.to_dict()
                article_data["content_type"] = ContentType.NEWS
                ArticleRepository.create(session, article_data)
                existing_hashes.add(article.content_hash)
                new_count += 1

            logger.info(f"신규 뉴스 {new_count}건 저장 완료")
            return new_count

    except Exception as e:
        logger.error(f"뉴스 수집 실패: {e}")
        return 0


def collect_papers() -> int:
    """논문 수집"""
    try:
        collector = PubMedCollector()

        with get_session() as session:
            new_count = 0

            papers = collector.collect_by_keywords(
                DEFAULT_PUBMED_KEYWORDS,
                max_per_keyword=20,
                days_back=7
            )

            for paper in papers:
                # PMID 중복 체크
                if paper.pmid and ArticleRepository.exists_by_pmid(session, paper.pmid):
                    continue

                if ArticleRepository.exists_by_link(session, paper.link):
                    continue

                # 저장
                paper_data = paper.to_dict()
                paper_data["content_type"] = ContentType.PAPER
                ArticleRepository.create(session, paper_data)
                new_count += 1

            logger.info(f"신규 논문 {new_count}건 저장 완료")
            return new_count

    except Exception as e:
        logger.error(f"논문 수집 실패: {e}")
        return 0


def process_articles() -> int:
    """AI 분석"""
    classifier = get_classifier()
    summarizer = get_summarizer()

    processed_count = 0

    with get_session() as session:
        unprocessed = ArticleRepository.get_unprocessed(session, limit=100)

        for article in unprocessed:
            try:
                # 카테고리 분류
                text = article.description or article.abstract or ""
                category = classifier.classify(article.title, text)

                # 요약 생성
                summary = summarizer.summarize(article.title, text)

                # 중요도 점수
                importance = summarizer.score_importance(article.title, text)

                # 저장
                ArticleRepository.update_analysis(
                    session,
                    article.id,
                    category,
                    summary,
                    importance
                )

                processed_count += 1
                logger.debug(f"분석 완료: {article.title[:30]}... [{category.value}]")

            except Exception as e:
                logger.error(f"기사 분석 실패: {e}")

    return processed_count


def generate_and_send_reports() -> int:
    """리포트 생성 및 발송"""
    generator = get_generator()
    sender = get_sender()

    if not sender.is_configured:
        logger.warning("이메일 설정이 완료되지 않아 발송을 건너뜁니다.")
        return 0

    sent_count = 0

    with get_session() as session:
        # 오늘 뉴스/논문 조회
        news = ArticleRepository.get_today_articles(
            session,
            content_type=ContentType.NEWS,
            processed_only=True
        )
        papers = ArticleRepository.get_today_articles(
            session,
            content_type=ContentType.PAPER,
            processed_only=True
        )

        if not news and not papers:
            logger.warning("발송할 콘텐츠가 없습니다.")
            return 0

        # 수신자 조회
        recipients = RecipientRepository.get_all_active(session)

        if not recipients:
            logger.warning("등록된 수신자가 없습니다.")
            return 0

        # 리포트 생성
        report_date = datetime.now()
        subject = f"[AllergyNewsLetter] {report_date.strftime('%Y-%m-%d')} 알러지 뉴스 브리핑"

        for recipient in recipients:
            try:
                # 중복 발송 체크
                if SendHistoryRepository.already_sent_today(session, recipient.id):
                    logger.debug(f"이미 발송됨: {recipient.email}")
                    continue

                # HTML 생성
                html_content = generator.generate_daily_report(
                    articles=news,
                    papers=papers,
                    report_date=report_date,
                    recipient_name=recipient.name
                )

                # 발송
                result = sender.send(
                    recipient=recipient.email,
                    subject=subject,
                    html_content=html_content
                )

                # 이력 저장
                SendHistoryRepository.create(
                    session,
                    recipient_id=recipient.id,
                    subject=subject,
                    article_count=len(news),
                    paper_count=len(papers),
                    report_date=report_date,
                    is_success=result.success,
                    error_message=result.error_message
                )

                if result.success:
                    sent_count += 1
                    logger.info(f"발송 성공: {recipient.email}")
                else:
                    logger.error(f"발송 실패: {recipient.email} - {result.error_message}")

            except Exception as e:
                logger.error(f"리포트 발송 중 오류: {e}")

    return sent_count


def send_newsletter_to_recipient(recipient_id: int) -> bool:
    """특정 수신자에게 당일 뉴스레터 발송 (신규 구독자용)"""
    generator = get_generator()
    sender = get_sender()

    if not sender.is_configured:
        logger.warning("이메일 설정이 완료되지 않아 발송을 건너뜁니다.")
        return False

    with get_session() as session:
        # 수신자 조회
        from .database.models import Recipient
        recipient = session.query(Recipient).filter(
            Recipient.id == recipient_id,
            Recipient.is_active == True
        ).first()

        if not recipient:
            logger.error(f"수신자를 찾을 수 없음: {recipient_id}")
            return False

        # 오늘 뉴스/논문 조회
        news = ArticleRepository.get_today_articles(
            session,
            content_type=ContentType.NEWS,
            processed_only=True
        )
        papers = ArticleRepository.get_today_articles(
            session,
            content_type=ContentType.PAPER,
            processed_only=True
        )

        if not news and not papers:
            logger.warning(f"발송할 콘텐츠가 없습니다: {recipient.email}")
            return False

        # 리포트 생성 및 발송
        try:
            report_date = datetime.now()
            subject = f"[AllergyNewsLetter] {report_date.strftime('%Y-%m-%d')} 알러지 뉴스 브리핑"

            html_content = generator.generate_daily_report(
                articles=news,
                papers=papers,
                report_date=report_date,
                recipient_name=recipient.name
            )

            result = sender.send(
                recipient=recipient.email,
                subject=subject,
                html_content=html_content
            )

            # 이력 저장
            SendHistoryRepository.create(
                session,
                recipient_id=recipient.id,
                subject=subject,
                article_count=len(news),
                paper_count=len(papers),
                report_date=report_date,
                is_success=result.success,
                error_message=result.error_message
            )

            if result.success:
                logger.info(f"신규 구독자 뉴스레터 발송 성공: {recipient.email}")
                return True
            else:
                logger.error(f"신규 구독자 뉴스레터 발송 실패: {recipient.email} - {result.error_message}")
                return False

        except Exception as e:
            logger.error(f"신규 구독자 리포트 발송 중 오류: {e}")
            return False


def run_scheduler():
    """스케줄러 실행"""
    logger.info("AllergyNewsLetter 스케줄러 시작")

    scheduler = BlockingScheduler()

    # 크롤링 작업 (오전 7시)
    scheduler.add_job(
        run_crawl_job,
        trigger=CronTrigger(hour=settings.crawl_hour, minute=settings.crawl_minute),
        id="crawl_job",
        name="Daily Crawling",
    )

    # 뉴스레터 발송 (오전 8시)
    scheduler.add_job(
        run_send_job,
        trigger=CronTrigger(hour=settings.send_hour, minute=settings.send_minute),
        id="send_job",
        name="Daily Newsletter",
    )

    logger.info(
        f"스케줄 설정: 크롤링 {settings.crawl_hour:02d}:{settings.crawl_minute:02d}, "
        f"발송 {settings.send_hour:02d}:{settings.send_minute:02d}"
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("스케줄러 종료")
        scheduler.shutdown()


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="AllergyNewsLetter - 알러지 뉴스/논문 브리핑")
    parser.add_argument("--run-once", action="store_true", help="즉시 한 번 실행")
    parser.add_argument("--collect-only", action="store_true", help="수집만 실행")
    parser.add_argument("--process-only", action="store_true", help="AI 분석만 실행")
    parser.add_argument("--send-only", action="store_true", help="발송만 실행")
    parser.add_argument("--web", action="store_true", help="웹 서버 실행")

    args = parser.parse_args()

    # 환경 변수 로드
    load_dotenv()

    # 로그 디렉토리 생성
    (settings.BASE_DIR / "logs").mkdir(exist_ok=True)

    # 데이터베이스 초기화
    logger.info("데이터베이스 초기화...")
    init_db(settings.database_url)

    if args.web:
        logger.info("웹 서버 모드")
        from .web.app import run_server
        run_server()
    elif args.collect_only:
        logger.info("수집만 실행")
        collect_news()
        collect_papers()
    elif args.process_only:
        logger.info("AI 분석만 실행")
        process_articles()
    elif args.send_only:
        logger.info("발송만 실행")
        generate_and_send_reports()
    elif args.run_once:
        logger.info("즉시 실행 모드")
        run_daily_job()
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
