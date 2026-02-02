@echo off
REM AllergyNewsLetter 발송만 실행
REM Windows Task Scheduler에서 사용 (오전 8시)

cd /d C:\GIT\AllergyNewsLetter

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python src/main.py --send-only

echo [%date% %time%] Send job completed >> logs\scheduler.log
