@echo off
REM AllergyNewsLetter 일일 실행 스크립트
REM Windows Task Scheduler에서 사용

cd /d C:\GIT\AllergyNewsLetter

REM 가상환경 활성화 (있는 경우)
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM 즉시 한 번 실행
python src/main.py --run-once

REM 로그 기록
echo [%date% %time%] Daily job completed >> logs\scheduler.log
