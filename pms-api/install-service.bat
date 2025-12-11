@echo off
setlocal enabledelayedexpansion

REM ====================================================
REM KTW PMS API - Windows Service Installer (Use NSSM)
REM ====================================================

REM 1. 取得當前目錄 (自動偵測)
cd /d "%~dp0"
set APP_DIR=%CD%

echo [INFO] 專案目錄: %APP_DIR%

REM 2. 自動偵測 Node.js 位置
set NODE_EXE=
where node >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%i in ('where node') do (
        set NODE_EXE=%%i
        goto :FOUND_NODE
    )
)

:FOUND_NODE
if "%NODE_EXE%"=="" (
    REM 找不到時的預設路徑
    set NODE_EXE=C:\Program Files\nodejs\node.exe
)
echo [INFO] Node.js 位置: %NODE_EXE%

REM 設定其他變數
set SERVICE_NAME=KTW_PMS_API
set DISPLAY_NAME=KTW Hotel PMS API
set APP_SCRIPT=%APP_DIR%\server.js
set LOG_DIR=%APP_DIR%\logs
set NSSM_EXE=%APP_DIR%\nssm.exe

echo.
echo ====================================================
echo   KTW PMS API Service Installer
echo ====================================================
echo.

REM 3. 檢查 Node.js 執行檔是否存在
if not exist "%NODE_EXE%" (
    echo [ERROR] 找不到 node.exe！
    echo 系統無法自動找到 Node.js，預設路徑也找不到。
    echo 請編輯此腳本，手動修改 NODE_EXE 的路徑。
    pause
    exit /b 1
)

REM 4. 檢查是否為管理員權限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] 請以系統管理員身分執行此腳本！
    echo 請對檔案點右鍵，選擇「以系統管理員身分執行」。
    pause
    exit /b 1
)

REM 5. 檢查 NSSM 是否存在
if not exist "%NSSM_EXE%" (
    echo [ERROR] 找不到 nssm.exe
    echo.
    echo 請確認 nssm.exe 是否已複製到:
    echo %APP_DIR%
    echo.
    pause
    exit /b 1
)

REM 6. 建立日誌資料夾
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
)

REM 7. 移除舊服務
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo [INFO] 服務 %SERVICE_NAME% 已存在，正在移除舊服務...
    "%NSSM_EXE%" stop %SERVICE_NAME%
    "%NSSM_EXE%" remove %SERVICE_NAME% confirm
    timeout /t 2 /nobreak >nul
)

REM 8. 安裝服務
echo [INFO] 安裝服務中...
"%NSSM_EXE%" install %SERVICE_NAME% "%NODE_EXE%" "%APP_SCRIPT%"
if %errorLevel% neq 0 (
    echo [ERROR] 安裝失敗！
    pause
    exit /b 1
)

REM 9. 設定服務參數
echo [INFO] 設定服務參數...
"%NSSM_EXE%" set %SERVICE_NAME% Description "Host KTW Hotel PMS API for Line Bot"
"%NSSM_EXE%" set %SERVICE_NAME% DisplayName "%DISPLAY_NAME%"
"%NSSM_EXE%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM_EXE%" set %SERVICE_NAME% AppDirectory "%APP_DIR%"
"%NSSM_EXE%" set %SERVICE_NAME% AppStdout "%LOG_DIR%\service.log"
"%NSSM_EXE%" set %SERVICE_NAME% AppStderr "%LOG_DIR%\error.log"
"%NSSM_EXE%" set %SERVICE_NAME% AppStopMethodSkip 0
"%NSSM_EXE%" set %SERVICE_NAME% AppStopMethodConsole 1500
"%NSSM_EXE%" set %SERVICE_NAME% AppRestartDelay 3000

REM 10. 啟動服務
echo [INFO] 啟動服務...
"%NSSM_EXE%" start %SERVICE_NAME%

echo.
echo ====================================================
echo   ✅ 安裝成功！服務已啟動
echo ====================================================
echo.
echo 服務名稱: %SERVICE_NAME%
echo 監控網址: http://localhost:3000/api/health
echo.
pause
