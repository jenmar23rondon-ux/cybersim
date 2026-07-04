@echo off
setlocal enabledelayedexpansion
title CyberSim - Validate
cd /d "%~dp0"

echo ================================================================
echo   CyberSim - Validacion local (mismo set que corre en CI)
echo ================================================================
echo.
set FAIL=0

REM --- 1. docker-compose.yml -------------------------------------
echo [1/3] Validando docker-compose.yml...
docker compose config --quiet
if errorlevel 1 ( echo       FALLO & set FAIL=1 ) else ( echo       OK )

REM --- 2. Frontend type-check ------------------------------------
echo [2/3] Type-check del dashboard...
pushd dashboard
if not exist node_modules ( echo       Instalando dependencias... & call npm ci --silent )
call npx tsc --noEmit
if errorlevel 1 ( echo       FALLO & set FAIL=1 ) else ( echo       OK )
popd

REM --- 3. Backend byte-compile ----------------------------------
echo [3/3] Byte-compile del backend...
where python >nul 2>&1
if errorlevel 1 (
    echo       [SKIP] Python no esta instalado localmente ^(igual corre en Docker/CI^).
) else (
    pushd backend
    python -m compileall -q app
    if errorlevel 1 ( echo       FALLO & set FAIL=1 ) else ( echo       OK )
    popd
)

echo.
if "%FAIL%"=="1" (
    echo ================================================================
    echo   RESULTADO: HUBO FALLOS. Revisa arriba.
    echo ================================================================
    exit /b 1
) else (
    echo ================================================================
    echo   RESULTADO: TODO OK
    echo ================================================================
)
pause
endlocal
