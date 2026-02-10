# AllergyNewsLetter 빠른 시작 가이드

## 환경 설정

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

## API 키 발급

### 네이버 검색 API (필수)
1. https://developers.naver.com 접속
2. 애플리케이션 등록 → 사용 API: `검색` 선택
3. Client ID / Secret 발급

### PubMed API (권장)
1. https://www.ncbi.nlm.nih.gov/account/ 접속
2. 계정 생성 후 API Key 발급
3. (API 키 없이도 동작하나 Rate Limit이 낮음)

### Gmail 앱 비밀번호 (필수)
1. https://myaccount.google.com/apppasswords
2. 2단계 인증 활성화 후 앱 비밀번호 생성

## 실행 방법

```bash
# 즉시 한 번 실행 (수집 → 분석 → 발송)
python src/main.py --run-once

# 스케줄러 실행 (매일 자동)
python src/main.py

# 수집만 실행
python src/main.py --collect-only

# AI 분석만 실행
python src/main.py --process-only

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

## 프로젝트 구조

```
AllergyNewsLetter/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   └── keywords.yaml      # 검색 키워드 설정
├── src/
│   ├── config.py           # 설정 관리
│   ├── main.py             # 메인 실행
│   ├── collector/           # 수집기 (네이버, PubMed)
│   ├── processor/           # 처리기 (분류, 요약, 중복제거)
│   ├── database/            # 데이터베이스 (모델, 저장소)
│   ├── reporter/            # 리포트 생성
│   ├── mailer/              # 이메일 발송
│   └── web/                 # 웹 서버 (구독 관리)
├── templates/               # 이메일 템플릿
├── docs/                    # 문서
├── tests/                   # 테스트
├── logs/                    # 로그
└── data/                    # SQLite DB
```

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
- [x] Docker 배포 설정
- [x] 테스트 코드 작성 (pytest)
- [x] 수신자 관리 스크립트
- [x] 설치 가이드 문서

### Phase 4: 고도화 (진행중)
- [x] 경쟁사 동향 분석 섹션
- [x] 뉴스 대분류 그룹화 (의학·연구 / 산업·생활)
- [ ] Ollama AI 요약 품질 고도화
- [ ] 주간 요약 리포트
- [ ] 수신자별 관심 카테고리 필터링
