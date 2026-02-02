# AllergyNewsLetter 배포 가이드

## 목차
1. [GitHub 저장소 설정](#1-github-저장소-설정)
2. [MacBook 초기 설정](#2-macbook-초기-설정)
3. [Self-hosted Runner 설정](#3-self-hosted-runner-설정)
4. [GitHub Secrets 설정](#4-github-secrets-설정)
5. [배포 워크플로우](#5-배포-워크플로우)
6. [운영 명령어](#6-운영-명령어)

---

## 1. GitHub 저장소 설정

### 1.1 저장소 생성 및 Push

```bash
# Windows에서 실행
cd C:\GIT\AllergyNewsLetter

# Git 초기화
git init
git branch -M master

# GitHub 저장소 연결
git remote add origin https://github.com/YOUR_USERNAME/AllergyNewsLetter.git

# 초기 커밋 및 Push
git add .
git commit -m "feat: initial commit - AllergyNewsLetter"
git push -u origin master

# prod 브랜치 생성
git checkout -b prod
git push -u origin prod
```

### 1.2 브랜치 전략

```
master (개발) → prod (배포)
     │              │
     │              └── GitHub Actions 자동 배포
     │
     └── 개발/테스트
```

---

## 2. MacBook 초기 설정

### 2.1 OrbStack 설치

```bash
# Homebrew로 설치
brew install orbstack

# 또는 공식 사이트에서 다운로드
# https://orbstack.dev
```

### 2.2 프로젝트 클론

```bash
# 프로젝트 디렉토리
cd ~
git clone https://github.com/YOUR_USERNAME/AllergyNewsLetter.git
cd AllergyNewsLetter

# prod 브랜치로 전환
git checkout prod
```

### 2.3 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 값 편집
nano .env
```

**.env 필수 설정:**
```ini
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

### 2.4 초기 실행

```bash
# 설정 스크립트 실행
chmod +x scripts/setup-macbook.sh
./scripts/setup-macbook.sh

# 또는 수동 실행
docker compose -f docker-compose.prod.yml up -d
```

---

## 3. Self-hosted Runner 설정

GitHub Actions가 MacBook에서 자동 배포하려면 Self-hosted Runner가 필요합니다.

### 3.1 Runner 설치

1. GitHub 저장소 → Settings → Actions → Runners
2. "New self-hosted runner" 클릭
3. macOS 선택 후 명령어 실행:

```bash
# 디렉토리 생성
mkdir -p ~/actions-runner && cd ~/actions-runner

# 다운로드 (버전은 GitHub에서 확인)
curl -o actions-runner-osx-x64-2.xxx.x.tar.gz -L https://github.com/actions/runner/releases/download/v2.xxx.x/actions-runner-osx-x64-2.xxx.x.tar.gz

# 압축 해제
tar xzf ./actions-runner-osx-x64-2.xxx.x.tar.gz

# 설정
./config.sh --url https://github.com/YOUR_USERNAME/AllergyNewsLetter --token YOUR_TOKEN

# 서비스로 설치 (자동 시작)
./svc.sh install
./svc.sh start
```

### 3.2 Runner 상태 확인

```bash
# 상태 확인
./svc.sh status

# 로그 확인
tail -f ~/actions-runner/_diag/Runner*.log
```

---

## 4. GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions

### 필수 Secrets

| Secret Name | 설명 | 예시 |
|-------------|------|------|
| `DEPLOY_PATH` | MacBook 프로젝트 경로 | `/Users/username/AllergyNewsLetter` |
| `NAVER_CLIENT_ID` | 네이버 API Client ID | `m2AAYZKJa...` |
| `NAVER_CLIENT_SECRET` | 네이버 API Secret | `5noat16...` |
| `GMAIL_ADDRESS` | Gmail 주소 | `your@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 | `xxxx xxxx xxxx xxxx` |
| `PUBMED_API_KEY` | PubMed API 키 (선택) | |
| `PUBMED_EMAIL` | PubMed 이메일 (선택) | |

---

## 5. 배포 워크플로우

### 5.1 자동 배포 (CI/CD)

```bash
# master에서 개발
git checkout master
# ... 코드 수정 ...
git add .
git commit -m "feat: 새로운 기능"
git push

# prod로 머지하여 배포
git checkout prod
git merge master
git push  # ← 자동 배포 트리거!
```

### 5.2 수동 배포

```bash
# MacBook에서 직접 실행
cd ~/AllergyNewsLetter
git pull origin prod
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 6. 운영 명령어

### 컨테이너 관리

```bash
# 상태 확인
docker compose -f docker-compose.prod.yml ps

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f

# 재시작
docker compose -f docker-compose.prod.yml restart

# 중지
docker compose -f docker-compose.prod.yml down

# 완전 재빌드
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

### 즉시 실행 (테스트)

```bash
# 컨테이너 내에서 즉시 실행
docker compose -f docker-compose.prod.yml exec allergynewsletter python src/main.py --run-once

# 수집만
docker compose -f docker-compose.prod.yml exec allergynewsletter python src/main.py --collect-only

# 발송만
docker compose -f docker-compose.prod.yml exec allergynewsletter python src/main.py --send-only
```

### 수신자 관리

```bash
# 수신자 추가
docker compose -f docker-compose.prod.yml exec allergynewsletter python scripts/add_recipient.py --email user@example.com --name "홍길동"

# 수신자 목록
docker compose -f docker-compose.prod.yml exec allergynewsletter python scripts/add_recipient.py --list
```

---

## 트러블슈팅

### Runner가 오프라인일 때

```bash
cd ~/actions-runner
./svc.sh status
./svc.sh start
```

### 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker compose -f docker-compose.prod.yml logs

# .env 파일 확인
cat .env

# 권한 확인
ls -la data/ logs/
```

### 이메일 발송 실패

1. Gmail 앱 비밀번호 확인
2. 2단계 인증 활성화 여부 확인
3. `.env` 파일의 `GMAIL_APP_PASSWORD` 값 확인
