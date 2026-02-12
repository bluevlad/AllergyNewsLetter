# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 상위 `C:/GIT/CLAUDE.md`의 Git-First Workflow를 상속합니다.

## Project Overview

AllergyNewsLetter - 알러지 뉴스/논문 브리핑 자동화 서비스 (PubMed 수집 → AI 요약 → 이메일 뉴스레터)

## Environment

- **Database**: SQLite (SQLAlchemy ORM)
- **Target Server**: MacBook Docker (172.30.1.72) / Windows 로컬 개발
- **Docker Strategy**: Docker Compose (scheduler + web)
- **Python Version**: 3.10+
- **AI**: Ollama (로컬 LLM), Claude API (선택적)

## Tech Stack

| 항목 | 기술 |
|------|------|
| Language | Python 3.10+ |
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0+ |
| Database | SQLite |
| Scheduler | APScheduler |
| AI/ML | Ollama (로컬), Anthropic Claude API (선택적) |
| HTTP Client | httpx, requests |
| Email | Gmail SMTP (aiosmtplib) |
| Template | Jinja2 |
| Config | Pydantic + python-dotenv |
| PubMed | Biopython |
| Web Scraping | BeautifulSoup4, lxml |

## Setup and Run Commands

```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# 실행 모드
python -m src.main              # 스케줄러 모드 (기본)
python -m src.main --web        # 웹 서버 모드
python -m src.main --run-once   # 1회 실행 (수집 → 발송)
python -m src.main --collect-only  # 수집만
python -m src.main --send-only     # 발송만

# Docker
docker compose up -d            # 개발
docker compose -f docker-compose.prod.yml up -d  # 운영

# 테스트
pytest tests/
```

Default server port: 4050

## Project Structure

```
AllergyNewsLetter/
├── src/
│   ├── main.py              # 엔트리포인트
│   ├── config.py            # Pydantic 설정
│   ├── collector/           # PubMed 논문/뉴스 수집
│   ├── database/            # SQLAlchemy 모델/세션
│   ├── mailer/              # 이메일 발송
│   ├── processor/           # AI 요약 (Ollama/Claude)
│   ├── reporter/            # 리포트 생성
│   └── web/                 # FastAPI 웹 앱 (구독 관리)
├── templates/               # 이메일 HTML 템플릿
├── config/                  # 설정 파일
├── tests/                   # 테스트
├── data/                    # SQLite DB (자동 생성)
└── logs/
```

## Do NOT

- .env 파일 커밋 금지
- requirements.txt에 없는 패키지를 설치 없이 import 금지
- pydantic v1 문법과 v2 문법 혼용 금지 (v2 사용)
- 서버 주소, 비밀번호 추측 금지 — 반드시 확인 후 사용
- 운영 Docker 컨테이너 직접 조작 금지 (allergynewsletter-scheduler, allergynewsletter-web)
- 자격증명(비밀번호, API 키)을 소스코드에 하드코딩하지 마라
- CORS에 allow_origins=["*"] 또는 origins="*" 사용하지 마라
- API 엔드포인트를 인증 없이 노출하지 마라
- console.log/print로 민감 정보를 출력하지 마라
- PubMed API 호출 시 날짜 형식 반드시 확인 (YYYY/MM/DD)

## Database Notes

- ORM: SQLAlchemy 2.0+ (async 미사용, 동기 세션)
- raw SQL 작성 시 SQLite 문법 사용

## Configuration

- 환경변수는 `.env` 파일로 관리
- `.env` 로딩: pydantic-settings
- PubMed 검색 파라미터: `config/` 하위 YAML

## Documentation

### 문서 참조 경로
- 프로젝트 관련 문서: `C:/GIT/Claude-Opus-bluevlad/docs/AllergyNewsLetter/`
- 기존 문서: QUICKSTART.md, SETUP.md, DEPLOYMENT.md, PROPOSAL.md, WBS.md, ENHANCEMENT_LOG.md

### 문서 작성 규칙
- 개발 중 새 문서는 `C:/GIT/Claude-Opus-bluevlad/docs/AllergyNewsLetter/`에 생성
- 프로젝트 루트에는 `README.md`와 `CLAUDE.md`만 유지

### 표준/컨벤션 참조
- Git 커밋: `C:/GIT/Claude-Opus-bluevlad/standards/git/COMMIT_CONVENTION.md`
- 브랜치: `C:/GIT/Claude-Opus-bluevlad/standards/git/BRANCH_CONVENTION.md`
- 서비스 정보: `C:/GIT/Claude-Opus-bluevlad/services/allergynewsletter/README.md`

## Deployment

- **CI/CD**: GitHub Actions (prod 브랜치 push 시 자동 배포)
- **브랜치 전략**: master (개발) → prod (배포)
- **운영 포트**: 4050
- **스케줄**: 크롤링 07:00, 발송 08:00
- **헬스체크**: http://localhost:4050/

> 로컬 환경 정보는 `CLAUDE.local.md` 참조 (git에 포함되지 않음)
