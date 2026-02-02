# AllergyNewsLetter

> 알러지 관련 뉴스 및 논문 일일 브리핑 자동화 서비스

## 프로젝트 개요

알러지 환자, 의료진, 연구자를 위한 **알러지 관련 최신 뉴스 및 논문 정보**를 매일 아침 이메일로 제공하는 자동화 서비스입니다.

### 주요 기능

- **뉴스 자동 수집**: 네이버 뉴스에서 알러지 관련 기사 수집
- **논문 자동 수집**: PubMed에서 최신 알러지 연구 논문 수집
- **AI 기반 분석**: 기사/논문 요약, 카테고리 분류, 중요도 산정
- **뉴스레터 발송**: HTML 형태의 일일 브리핑 자동 발송

## 시스템 아키텍처

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
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │    Mailer     │
        │  - Gmail 발송 │
        └───────────────┘
```

## 기술 스택

| 구성요소 | 기술 |
|---------|------|
| 언어 | Python 3.10+ |
| 뉴스 수집 | 네이버 검색 API |
| 논문 수집 | PubMed E-utilities API |
| AI 요약 | Ollama (로컬) / Claude API (선택) |
| 스케줄러 | APScheduler |
| DB | SQLite |
| 이메일 | Gmail SMTP |

## 프로젝트 구조

```
AllergyNewsLetter/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   ├── keywords.yaml      # 검색 키워드 설정
│   └── recipients.yaml    # 수신자 설정
├── src/
│   ├── config.py          # 설정 관리
│   ├── main.py            # 메인 실행
│   ├── collector/         # 수집기
│   │   ├── base.py        # 공통 인터페이스
│   │   ├── naver_news.py  # 네이버 뉴스
│   │   └── pubmed.py      # PubMed 논문
│   ├── processor/         # 처리기
│   │   ├── classifier.py  # 카테고리 분류
│   │   ├── summarizer.py  # AI 요약
│   │   └── deduplicator.py
│   ├── database/          # 데이터베이스
│   │   ├── models.py
│   │   └── repository.py
│   ├── reporter/          # 리포트 생성
│   └── mailer/            # 이메일 발송
├── templates/             # 이메일 템플릿
├── tests/
├── logs/
└── data/
```

## 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
cd C:\GIT\AllergyNewsLetter

# 가상환경 생성 (선택)
python -m venv .venv
.venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
copy .env.example .env
# .env 파일을 열어 API 키 설정
```

### 2. API 키 발급

#### 네이버 검색 API (필수)
1. https://developers.naver.com 접속
2. 애플리케이션 등록
3. Client ID / Secret 발급

#### PubMed API (권장)
1. https://www.ncbi.nlm.nih.gov/account/ 접속
2. 계정 생성 후 API Key 발급
3. (API 키 없이도 동작하나 Rate Limit이 낮음)

#### Gmail 앱 비밀번호 (필수)
1. https://myaccount.google.com/apppasswords
2. 앱 비밀번호 생성

### 3. 실행

```bash
# 즉시 한 번 실행
python src/main.py --run-once

# 스케줄러 실행 (매일 자동)
python src/main.py

# 수집만 실행
python src/main.py --collect-only

# 발송만 실행
python src/main.py --send-only
```

## 카테고리 분류

| 카테고리 | 설명 |
|---------|------|
| 임상/치료 | 신약, 치료법, 가이드라인 |
| 연구/학술 | 논문, 학회, 연구 결과 |
| 생활/관리 | 식단, 환경, 예방법 |
| 산업/시장 | 제약사, 시장 동향 |
| 규제/정책 | 식약처, FDA, 정책 |

## 문서

- [기술 제안서](docs/PROPOSAL.md)
- [설치 가이드](docs/SETUP.md)

## 개발 현황

### Phase 1: 기반 구축 (완료)
- [x] 프로젝트 스캐폴딩
- [x] 알러지 키워드 설정
- [x] 수집기 공통 인터페이스
- [x] 네이버 뉴스 수집기
- [x] PubMed 논문 수집기

### Phase 2: 핵심 구현 (완료)
- [x] 알러지 분류기 (키워드 + Ollama AI)
- [x] AI 요약기 (Ollama 기반)
- [x] 중복 탐지기
- [x] 이메일 템플릿 (뉴스 + 논문 통합)
- [x] Gmail 메일러
- [x] 리포트 생성기
- [x] main.py 전체 파이프라인

### Phase 3: 통합 및 배포 (완료)
- [x] Docker 배포 설정 (Dockerfile, docker-compose.yml)
- [x] Windows Task Scheduler 연동 (PowerShell 스크립트)
- [x] 테스트 코드 작성 (pytest 기반)
- [x] 수신자 관리 스크립트 (add_recipient.py)
- [x] 설치 가이드 문서 (docs/SETUP.md)

## 라이선스

Private - All Rights Reserved
