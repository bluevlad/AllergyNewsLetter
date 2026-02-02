# AllergyNewsLetter 설치 및 설정 가이드

## 목차
1. [사전 요구사항](#사전-요구사항)
2. [설치](#설치)
3. [API 키 발급](#api-키-발급)
4. [환경 설정](#환경-설정)
5. [실행 방법](#실행-방법)
6. [배포 옵션](#배포-옵션)

---

## 사전 요구사항

### 필수
- Python 3.10 이상
- 네이버 개발자 계정 (검색 API)
- Gmail 계정 (앱 비밀번호)

### 선택
- PubMed API 키 (논문 수집 속도 향상)
- Ollama (AI 요약/분류)
- Docker (컨테이너 배포)

---

## 설치

### 1. 저장소 클론 또는 다운로드

```bash
cd C:\GIT
git clone <repository-url> AllergyNewsLetter
cd AllergyNewsLetter
```

### 2. 가상환경 생성 (권장)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

---

## API 키 발급

### 1. 네이버 검색 API (필수)

1. https://developers.naver.com 접속
2. 로그인 → 애플리케이션 등록
3. 애플리케이션 이름: `AllergyNewsLetter`
4. 사용 API: `검색` 선택
5. 등록 후 **Client ID** / **Client Secret** 복사

### 2. PubMed API (권장)

1. https://www.ncbi.nlm.nih.gov/account/ 접속
2. NCBI 계정 생성/로그인
3. Settings → API Key Management
4. Create an API Key
5. API Key 복사

> API 키 없이도 동작하지만, Rate Limit이 3 req/sec로 제한됩니다.
> API 키가 있으면 10 req/sec까지 가능합니다.

### 3. Gmail 앱 비밀번호 (필수)

1. https://myaccount.google.com 접속
2. 보안 → 2단계 인증 활성화 (필수)
3. 보안 → 앱 비밀번호
4. 앱 선택: `메일`, 기기 선택: `Windows 컴퓨터`
5. 생성된 16자리 비밀번호 복사

---

## 환경 설정

### 1. 환경 변수 파일 생성

```bash
copy .env.example .env
```

### 2. .env 파일 편집

```ini
# 네이버 API (필수)
NAVER_CLIENT_ID=발급받은_클라이언트_ID
NAVER_CLIENT_SECRET=발급받은_클라이언트_시크릿

# PubMed API (권장)
PUBMED_API_KEY=발급받은_API_KEY
PUBMED_EMAIL=your_email@example.com

# Gmail (필수)
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=발급받은_앱_비밀번호

# Ollama (선택 - 로컬 AI)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# 스케줄러 (기본값)
CRAWL_HOUR=7
CRAWL_MINUTE=0
SEND_HOUR=8
SEND_MINUTE=0
```

### 3. 수신자 등록

```bash
# 수신자 추가
python scripts/add_recipient.py --email user@example.com --name "홍길동"

# 그룹 지정 (PATIENT, MEDICAL, RESEARCHER, ALL)
python scripts/add_recipient.py --email doctor@hospital.com --name "김의사" --group MEDICAL

# 수신자 목록 확인
python scripts/add_recipient.py --list
```

---

## 실행 방법

### 1. 즉시 실행 (테스트)

```bash
# 전체 파이프라인 (수집 → 분석 → 발송)
python src/main.py --run-once

# 수집만
python src/main.py --collect-only

# 분석만
python src/main.py --process-only

# 발송만
python src/main.py --send-only
```

### 2. 스케줄러 실행

```bash
# 매일 자동 실행 (오전 7시 수집, 8시 발송)
python src/main.py
```

### 3. 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 특정 테스트
pytest tests/test_classifier.py -v
```

---

## 배포 옵션

### 옵션 A: Windows Task Scheduler (권장)

PowerShell 관리자 권한으로 실행:

```powershell
# 스케줄러 등록
.\scripts\setup_scheduler.ps1

# 스케줄러 제거
.\scripts\remove_scheduler.ps1
```

등록되는 작업:
- `AllergyNewsLetter-Collect`: 매일 오전 7시 수집
- `AllergyNewsLetter-Send`: 매일 오전 8시 발송

### 옵션 B: Docker

```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

### 옵션 C: 백그라운드 실행 (nohup)

Linux/Mac:
```bash
nohup python src/main.py > logs/nohup.log 2>&1 &
```

---

## 문제 해결

### 네이버 API 오류

```
ValueError: 네이버 API 인증 정보가 필요합니다.
```
→ `.env` 파일의 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 확인

### Gmail 발송 실패

```
SMTPAuthenticationError: Gmail 인증 실패
```
→ Gmail 2단계 인증 활성화 및 앱 비밀번호 사용 확인

### Ollama 연결 실패

```
Ollama 서버 연결 실패
```
→ Ollama 실행 여부 확인: `ollama serve`
→ 또는 AI 기능 없이 키워드 기반 분류로 동작

### PubMed Rate Limit

```
HTTP 429 Too Many Requests
```
→ API 키 발급 권장 (10 req/sec로 증가)

---

## 로그 위치

- `logs/allergynewsletter.log`: 메인 로그
- `logs/scheduler.log`: 스케줄러 실행 로그

---

## 데이터 위치

- `data/allergynewsletter.db`: SQLite 데이터베이스
- `config/keywords.yaml`: 검색 키워드 설정
- `config/recipients.yaml`: 초기 수신자 설정
