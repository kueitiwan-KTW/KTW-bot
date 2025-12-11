@echo off
setlocal
cd /d "%~dp0"
set SERVICE_NAME=KTW_PMS_API

REM Check Admin Rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Please run as Administrator!
    echo Right-click -> Run as Administrator.
    pause
    exit /b 1
)

:MENU
cls
echo ====================================================
echo   KTW PMS API Manager
echo ====================================================
echo.
echo   1. Start Service
echo   2. Stop Service
echo   3. Restart Service
echo   4. Check Status
echo   5. Exit
echo.
set /p CHOICE="Enter choice (1-5): "

if "%CHOICE%"=="1" goto START_SVC
if "%CHOICE%"=="2" goto STOP_SVC
if "%CHOICE%"=="3" goto RESTART_SVC
if "%CHOICE%"=="4" goto STATUS_SVC
if "%CHOICE%"=="5" goto END

goto MENU

:START_SVC
echo.
echo Starting %SERVICE_NAME% ...
net start %SERVICE_NAME%
pause
goto MENU

:STOP_SVC
echo.
echo Stopping %SERVICE_NAME% ...
net stop %SERVICE_NAME%
pause
goto MENU

:RESTART_SVC
echo.
echo Restarting %SERVICE_NAME% ...
net stop %SERVICE_NAME%
timeout /t 2 >nul
net start %SERVICE_NAME%
pause
goto MENU

:STATUS_SVC
echo.
echo --- Service State ---
sc query %SERVICE_NAME% | findstr "STATE"
echo.
echo --- API Health Check ---
curl -s http://localhost:3000/api/health
echo.
pause
goto MENU

:END
exit
