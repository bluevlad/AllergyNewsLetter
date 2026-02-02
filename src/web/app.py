"""
AllergyNewsLetter 웹 애플리케이션
이메일 인증 기반 구독 시스템
"""

import random
import string
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import settings
from ..database.models import Base, Recipient, EmailVerification, RecipientGroup
from ..mailer.gmail_sender import GmailSender

# 로깅 설정
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="AllergyNewsLetter",
    description="알러지 뉴스 & 논문 브리핑 구독 서비스",
    version="1.0.0"
)

# 템플릿 설정
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# 이메일 템플릿 설정
email_templates_dir = settings.BASE_DIR / "templates"
email_templates = Jinja2Templates(directory=str(email_templates_dir))

# 데이터베이스 설정
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)

# 테이블 생성
Base.metadata.create_all(bind=engine)

# Gmail 발송기
gmail_sender = GmailSender()


def get_db():
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_verification_code() -> str:
    """6자리 인증코드 생성"""
    return ''.join(random.choices(string.digits, k=settings.verification_code_length))


def generate_unsubscribe_token(email: str) -> str:
    """구독 해지 토큰 생성 (SHA256)"""
    data = f"{email}{secrets.token_hex(16)}{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def send_verification_email(email: str, name: str, code: str) -> bool:
    """인증코드 이메일 발송"""
    try:
        # 이메일 템플릿 렌더링
        template = email_templates.get_template("verification_code.html")
        html_content = template.render(
            email=email,
            name=name,
            code=code
        )

        subject = f"[AllergyNewsLetter] 인증코드: {code}"

        result = gmail_sender.send(
            to_email=email,
            subject=subject,
            html_content=html_content
        )

        return result.success
    except Exception as e:
        logger.error(f"인증 이메일 발송 실패: {e}")
        return False


def send_newsletter_to_new_subscriber(recipient_id: int):
    """신규 구독자에게 당일 뉴스레터 발송"""
    try:
        # main.py의 발송 로직 임포트 및 실행
        from ..main import send_newsletter_to_recipient
        send_newsletter_to_recipient(recipient_id)
        logger.info(f"신규 구독자 뉴스레터 발송 완료: recipient_id={recipient_id}")
    except Exception as e:
        logger.error(f"신규 구독자 뉴스레터 발송 실패: {e}")


# ==================== 라우트 ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """홈 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/subscribe", response_class=HTMLResponse)
async def subscribe_form(request: Request):
    """구독 신청 폼"""
    return templates.TemplateResponse("subscribe.html", {"request": request})


@app.post("/subscribe", response_class=HTMLResponse)
async def subscribe_submit(
    request: Request,
    email: str = Form(...),
    name: str = Form(default="")
):
    """구독 신청 처리 - 인증코드 발송"""
    email = email.strip().lower()
    name = name.strip()

    db = SessionLocal()
    try:
        # 이미 구독 중인지 확인
        existing = db.query(Recipient).filter(
            Recipient.email == email,
            Recipient.is_active == True
        ).first()

        if existing:
            return templates.TemplateResponse("subscribe.html", {
                "request": request,
                "error": "이미 구독 중인 이메일입니다.",
                "email": email,
                "name": name
            })

        # 인증코드 생성
        code = generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=settings.verification_expiry_minutes)

        # 기존 미인증 요청 삭제
        db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.is_verified == False
        ).delete()

        # 새 인증 레코드 생성
        verification = EmailVerification(
            email=email,
            name=name,
            code=code,
            expires_at=expires_at
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)

        # 인증 이메일 발송
        if send_verification_email(email, name, code):
            logger.info(f"인증코드 발송 완료: {email}")
            return RedirectResponse(
                url=f"/verify/{verification.id}?email={email}",
                status_code=303
            )
        else:
            return templates.TemplateResponse("subscribe.html", {
                "request": request,
                "error": "이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.",
                "email": email,
                "name": name
            })

    finally:
        db.close()


@app.get("/verify/{verification_id}", response_class=HTMLResponse)
async def verify_form(request: Request, verification_id: int, email: str = ""):
    """인증코드 입력 폼"""
    return templates.TemplateResponse("verify.html", {
        "request": request,
        "verification_id": verification_id,
        "email": email
    })


@app.post("/verify", response_class=HTMLResponse)
async def verify_submit(
    request: Request,
    verification_id: int = Form(...),
    email: str = Form(...),
    code: str = Form(...)
):
    """인증코드 확인"""
    code = code.strip()

    db = SessionLocal()
    try:
        verification = db.query(EmailVerification).filter(
            EmailVerification.id == verification_id,
            EmailVerification.email == email
        ).first()

        if not verification:
            return templates.TemplateResponse("verify.html", {
                "request": request,
                "verification_id": verification_id,
                "email": email,
                "error": "인증 정보를 찾을 수 없습니다. 다시 신청해주세요."
            })

        # 만료 확인
        if datetime.utcnow() > verification.expires_at:
            return templates.TemplateResponse("verify.html", {
                "request": request,
                "verification_id": verification_id,
                "email": email,
                "error": "인증코드가 만료되었습니다. 다시 신청해주세요."
            })

        # 시도 횟수 확인
        if verification.attempts >= settings.max_verification_attempts:
            return templates.TemplateResponse("verify.html", {
                "request": request,
                "verification_id": verification_id,
                "email": email,
                "error": "인증 시도 횟수를 초과했습니다. 다시 신청해주세요."
            })

        # 코드 확인
        if verification.code != code:
            verification.attempts += 1
            db.commit()
            remaining = settings.max_verification_attempts - verification.attempts
            return templates.TemplateResponse("verify.html", {
                "request": request,
                "verification_id": verification_id,
                "email": email,
                "error": f"인증코드가 일치하지 않습니다. (남은 시도: {remaining}회)"
            })

        # 인증 성공
        verification.is_verified = True
        db.commit()

        # 구독자 등록
        unsubscribe_token = generate_unsubscribe_token(email)

        # 기존 비활성 구독자 확인
        existing = db.query(Recipient).filter(Recipient.email == email).first()
        if existing:
            existing.is_active = True
            existing.name = verification.name or existing.name
            existing.unsubscribe_token = unsubscribe_token
            existing.updated_at = datetime.utcnow()
            recipient = existing
        else:
            recipient = Recipient(
                email=email,
                name=verification.name,
                group=RecipientGroup.ALL,
                unsubscribe_token=unsubscribe_token
            )
            db.add(recipient)

        db.commit()
        db.refresh(recipient)

        logger.info(f"신규 구독자 등록 완료: {email}")

        # 당일 뉴스레터 발송 (비동기적으로)
        try:
            send_newsletter_to_new_subscriber(recipient.id)
        except Exception as e:
            logger.error(f"즉시 발송 실패: {e}")

        return RedirectResponse(url=f"/result?email={email}", status_code=303)

    finally:
        db.close()


@app.post("/resend", response_class=HTMLResponse)
async def resend_code(
    request: Request,
    verification_id: int = Form(...)
):
    """인증코드 재발송"""
    db = SessionLocal()
    try:
        verification = db.query(EmailVerification).filter(
            EmailVerification.id == verification_id
        ).first()

        if not verification:
            return RedirectResponse(url="/subscribe", status_code=303)

        # 새 코드 생성
        new_code = generate_verification_code()
        verification.code = new_code
        verification.attempts = 0
        verification.expires_at = datetime.utcnow() + timedelta(minutes=settings.verification_expiry_minutes)
        db.commit()

        # 이메일 발송
        if send_verification_email(verification.email, verification.name, new_code):
            logger.info(f"인증코드 재발송 완료: {verification.email}")

        return RedirectResponse(
            url=f"/verify/{verification_id}?email={verification.email}",
            status_code=303
        )

    finally:
        db.close()


@app.get("/result", response_class=HTMLResponse)
async def result_page(request: Request, email: str = ""):
    """구독 완료 페이지"""
    return templates.TemplateResponse("result.html", {
        "request": request,
        "email": email
    })


@app.get("/unsubscribe/{token}", response_class=HTMLResponse)
async def unsubscribe_form(request: Request, token: str):
    """구독 해지 확인 페이지"""
    db = SessionLocal()
    try:
        recipient = db.query(Recipient).filter(
            Recipient.unsubscribe_token == token,
            Recipient.is_active == True
        ).first()

        if not recipient:
            return templates.TemplateResponse("unsubscribe.html", {
                "request": request,
                "error": "유효하지 않은 링크이거나 이미 해지된 구독입니다."
            })

        return templates.TemplateResponse("unsubscribe.html", {
            "request": request,
            "email": recipient.email,
            "token": token
        })

    finally:
        db.close()


@app.post("/unsubscribe/{token}", response_class=HTMLResponse)
async def unsubscribe_submit(request: Request, token: str):
    """구독 해지 처리"""
    db = SessionLocal()
    try:
        recipient = db.query(Recipient).filter(
            Recipient.unsubscribe_token == token,
            Recipient.is_active == True
        ).first()

        if not recipient:
            return templates.TemplateResponse("unsubscribe.html", {
                "request": request,
                "error": "유효하지 않은 링크이거나 이미 해지된 구독입니다."
            })

        email = recipient.email
        recipient.is_active = False
        recipient.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"구독 해지 완료: {email}")

        return templates.TemplateResponse("unsubscribe.html", {
            "request": request,
            "success": True,
            "email": email
        })

    finally:
        db.close()


# ==================== 서버 실행 ====================

def run_server():
    """웹 서버 실행"""
    import uvicorn

    logger.info(f"웹 서버 시작: http://{settings.web_host}:{settings.web_port}")
    uvicorn.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
