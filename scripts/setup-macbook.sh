#!/bin/bash
# MacBook (OrbStack) 초기 설정 스크립트

set -e

echo "🍎 AllergyNewsLetter MacBook 설정 시작"
echo "================================================"

# 1. 프로젝트 디렉토리 확인
PROJECT_DIR="${1:-$HOME/AllergyNewsLetter}"
echo "📁 프로젝트 경로: $PROJECT_DIR"

# 2. 필수 디렉토리 생성
echo "📂 디렉토리 생성..."
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/config"

# 3. .env 파일 확인
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo "   .env.example을 복사하고 값을 설정하세요:"
    echo ""
    echo "   cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env"
    echo "   nano $PROJECT_DIR/.env"
    echo ""
    exit 1
fi

# 4. Docker 확인 (OrbStack)
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다."
    echo "   OrbStack을 설치하세요: https://orbstack.dev"
    exit 1
fi

echo "✅ Docker 확인 완료: $(docker --version)"

# 5. Docker Compose 빌드 및 실행
echo "🐳 Docker 컨테이너 빌드 중..."
cd "$PROJECT_DIR"
docker compose -f docker-compose.prod.yml build

echo "🚀 컨테이너 시작..."
docker compose -f docker-compose.prod.yml up -d

# 6. 상태 확인
echo ""
echo "================================================"
echo "✅ 설정 완료!"
echo ""
echo "📊 컨테이너 상태:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "📜 로그 확인:"
echo "   docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🛑 중지:"
echo "   docker compose -f docker-compose.prod.yml down"
echo "================================================"
