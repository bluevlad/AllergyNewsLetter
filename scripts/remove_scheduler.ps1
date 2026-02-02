# AllergyNewsLetter Task Scheduler 제거 스크립트
# 관리자 권한으로 실행 필요

$ErrorActionPreference = "Stop"

Write-Host "AllergyNewsLetter Task Scheduler 제거" -ForegroundColor Yellow
Write-Host "=" * 50

$Tasks = @("AllergyNewsLetter-Collect", "AllergyNewsLetter-Send")

foreach ($TaskName in $Tasks) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[OK] $TaskName 작업 제거됨" -ForegroundColor Green
    } else {
        Write-Host "[SKIP] $TaskName 작업 없음" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "모든 AllergyNewsLetter 작업이 제거되었습니다." -ForegroundColor Cyan
