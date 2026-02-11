# AllergyNewsLetter

> 알러지 관련 뉴스 및 논문 일일 브리핑 자동화 서비스

알러지 환자, 의료진, 연구자를 위한 **알러지 관련 최신 뉴스 및 논문 정보**를 매일 아침 이메일로 제공하는 자동화 서비스입니다.

## 주요 기능

- **뉴스 자동 수집** — 네이버 뉴스에서 알러지 관련 기사 수집
- **논문 자동 수집** — PubMed에서 최신 알러지 연구 논문 수집
- **AI 기반 분석** — 기사/논문 요약, 카테고리 분류, 중요도 산정
- **기업 동향 분석** — 등록된 기업들의 뉴스 동향 비교 분석
- **뉴스레터 발송** — HTML 형태의 일일 브리핑 자동 발송

## 시스템 구성

```
┌──────────────┐  ┌──────────────┐
│ 네이버 뉴스   │  │  PubMed API  │
│  Collector   │  │  Collector   │
└──────┬───────┘  └──────┬───────┘
       │                  │
       └─────────┬────────┘
                 ▼
        ┌───────────────┐
        │   Processor   │
        │  - 중복 제거   │
        │  - AI 분류    │
        │  - 요약 생성   │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │   Reporter    │
        │  - 템플릿 생성 │
        │  - 동향 분석   │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │    Mailer     │
        │  - Gmail 발송 │
        └───────────────┘
```

### 기술 스택

| 구성요소 | 기술 |
|---------|------|
| 언어 | Python 3.10+ |
| 뉴스 수집 | 네이버 검색 API |
| 논문 수집 | PubMed E-utilities API |
| AI 분석 | Ollama (qwen2.5:7b) |
| DB | SQLite |
| 이메일 | Gmail SMTP |
| 스케줄러 | APScheduler |
| 배포 | Docker Compose |

### 뉴스레터 구성

| 섹션 | 설명 |
|------|------|
| ⭐ 오늘의 주요 뉴스 | 중요도 상위 3건 |
| 📊 기업 동향 분석 | 등록된 기업들의 뉴스 동향 비교 |
| 🔬 의학·연구 소식 | 임상/치료 + 연구/학술 통합 |
| 📋 산업·생활 소식 | 생활/관리 + 산업/시장 + 규제/정책 통합 |
| 📚 최신 논문 | PubMed 논문 |

## 테스트 계정

| 항목 | 값 | 비고 |
|------|---|------|
| 발송 계정 | `GMAIL_ADDRESS` (.env) | Gmail 앱 비밀번호 필요 |
| 네이버 API | `NAVER_CLIENT_ID` / `SECRET` (.env) | [개발자센터](https://developers.naver.com) |
| PubMed API | `PUBMED_API_KEY` (.env) | 선택 (없어도 동작) |
| AI 모델 | Ollama `qwen2.5:7b` | 선택 (없으면 키워드 기반 분석) |
| DB | `data/allergynewsletter.db` | SQLite, 자동 생성 |
| 웹 서버 | `http://localhost:4050` | 구독 관리 페이지 |

> 환경 변수 상세는 [.env.example](.env.example) 참조

## 문서

상세 문서는 [Claude-Opus-bluevlad/docs/AllergyNewsLetter](../Claude-Opus-bluevlad/docs/AllergyNewsLetter/) 에서 관리합니다.

| 문서 | 설명 |
|------|------|
| [빠른 시작](../Claude-Opus-bluevlad/docs/AllergyNewsLetter/QUICKSTART.md) | 설치, 실행, 프로젝트 구조, 개발 현황 |
| [설치 가이드](../Claude-Opus-bluevlad/docs/AllergyNewsLetter/SETUP.md) | 상세 설치/설정/문제 해결 |
| [배포 가이드](../Claude-Opus-bluevlad/docs/AllergyNewsLetter/DEPLOYMENT.md) | Docker, GitHub Actions, 운영 명령어 |
| [기술 제안서](../Claude-Opus-bluevlad/docs/AllergyNewsLetter/PROPOSAL.md) | 프로젝트 설계 문서 |
| [고도화 이력](../Claude-Opus-bluevlad/docs/AllergyNewsLetter/ENHANCEMENT_LOG.md) | 기능 고도화 변경 내역 |
| [WBS](../Claude-Opus-bluevlad/docs/AllergyNewsLetter/WBS.md) | 작업 분해 구조 및 진행 상태 |

## 라이선스

Private - All Rights Reserved
