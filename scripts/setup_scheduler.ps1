# AllergyNewsLetter Windows Task Scheduler 설정 스크립트
# 관리자 권한으로 실행 필요

param(
    [string]$ProjectPath = "C:\GIT\AllergyNewsLetter"
)

$ErrorActionPreference = "Stop"

Write-Host "AllergyNewsLetter Task Scheduler 설정" -ForegroundColor Cyan
Write-Host "=" * 50

# 1. 수집 작업 (오전 7시)
$CollectTaskName = "AllergyNewsLetter-Collect"
$CollectAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ProjectPath\scripts\run_collect.bat`""
$CollectTrigger = New-ScheduledTaskTrigger -Daily -At 7:00AM
$CollectSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

# 기존 작업 삭제
if (Get-ScheduledTask -TaskName $CollectTaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $CollectTaskName -Confirm:$false
    Write-Host "기존 $CollectTaskName 작업 삭제됨"
}

Register-ScheduledTask -TaskName $CollectTaskName -Action $CollectAction -Trigger $CollectTrigger -Settings $CollectSettings -Description "AllergyNewsLetter 뉴스/논문 수집 (매일 오전 7시)"
Write-Host "[OK] $CollectTaskName 작업 등록 완료 (매일 오전 7시)" -ForegroundColor Green

# 2. 발송 작업 (오전 8시)
$SendTaskName = "AllergyNewsLetter-Send"
$SendAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ProjectPath\scripts\run_send.bat`""
$SendTrigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
$SendSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

if (Get-ScheduledTask -TaskName $SendTaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $SendTaskName -Confirm:$false
    Write-Host "기존 $SendTaskName 작업 삭제됨"
}

Register-ScheduledTask -TaskName $SendTaskName -Action $SendAction -Trigger $SendTrigger -Settings $SendSettings -Description "AllergyNewsLetter 뉴스레터 발송 (매일 오전 8시)"
Write-Host "[OK] $SendTaskName 작업 등록 완료 (매일 오전 8시)" -ForegroundColor Green

Write-Host ""
Write-Host "=" * 50
Write-Host "설정 완료!" -ForegroundColor Cyan
Write-Host ""
Write-Host "등록된 작업:"
Get-ScheduledTask -TaskName "AllergyNewsLetter*" | Format-Table TaskName, State, Description -AutoSize
