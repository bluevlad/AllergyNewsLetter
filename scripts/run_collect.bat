@echo off
REM AllergyNewsLetter 수집만 실행
REM Windows Task Scheduler에서 사용 (오전 7시)

cd /d C:\GIT\AllergyNewsLetter

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python src/main.py --collect-only

echo [%date% %time%] Collect job completed >> logs\scheduler.log
