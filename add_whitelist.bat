@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if "%1"=="" (
    echo [INFO] 현재 내 PC 공인 IP를 자동으로 조회하여 원격 DB 화이트리스트에 등록합니다...
    python manage_db_whitelist.py add
) else if "%1"=="list" (
    python manage_db_whitelist.py list
) else if "%1"=="remove" (
    python manage_db_whitelist.py remove %2
) else if "%1"=="lockdown" (
    python manage_db_whitelist.py secure-lockdown
) else (
    python manage_db_whitelist.py add %1
)

pause
