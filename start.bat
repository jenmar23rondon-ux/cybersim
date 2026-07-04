@echo off
setlocal enabledelayedexpansion
title CyberSim - Ethical Attack Simulator
cd /d "%~dp0"

echo ================================================================
echo   CyberSim - Ethical Attack Simulator
echo   Local lab only. All attacks run against local containers.
echo ================================================================
echo.

REM --- 1. Check Docker is installed -------------------------------
where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no esta instalado o no esta en el PATH.
    echo         Instala Docker Desktop: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

REM --- 2. Check Docker daemon is running --------------------------
echo [1/4] Verificando que Docker este corriendo...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop no esta corriendo. Abrelo y espera a que
    echo         diga "Running", luego vuelve a ejecutar este .bat.
    echo.
    pause
    exit /b 1
)
echo       OK - Docker esta activo.

REM --- 3. Create .env from template if missing --------------------
echo [2/4] Preparando configuracion (.env)...
if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo       Creado .env desde .env.example.
        echo       ^(Opcional^) edita .env para agregar OPENAI_API_KEY o el webhook de SecureWatch.
    ) else (
        echo [ERROR] No se encontro .env.example. Estas en la carpeta correcta?
        pause
        exit /b 1
    )
) else (
    echo       OK - .env ya existe, se respeta.
)

REM --- 4. Build and start the whole stack -------------------------
echo [3/4] Construyendo y levantando contenedores ^(puede tardar la primera vez^)...
echo.

REM Use "docker compose" (v2) if available, else fall back to "docker-compose".
docker compose version >nul 2>&1
if errorlevel 1 (
    set "COMPOSE=docker-compose"
) else (
    set "COMPOSE=docker compose"
)

%COMPOSE% up --build -d
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo al levantar los contenedores. Revisa el log de arriba.
    pause
    exit /b 1
)

REM --- 5. Wait for the backend to answer /health -----------------
echo.
echo [4/4] Esperando a que el backend responda...
set /a tries=0
:waitloop
set /a tries+=1
curl -s -o nul -w "%%{http_code}" http://localhost:8000/health > "%TEMP%\cybersim_health.txt" 2>nul
set /p CODE=<"%TEMP%\cybersim_health.txt"
if "!CODE!"=="200" goto ready
if !tries! GEQ 30 goto timeout
timeout /t 2 /nobreak >nul
echo       ...intento !tries!/30
goto waitloop

:timeout
echo       [AVISO] El backend aun no responde en /health, pero los contenedores
echo               estan levantados. Dale unos segundos mas y refresca el dashboard.
goto open

:ready
echo       OK - Backend listo en http://localhost:8000

:open
echo.
echo ================================================================
echo   CyberSim esta corriendo!
echo ----------------------------------------------------------------
echo   Dashboard      : http://localhost:5173
echo   API / Swagger  : http://localhost:8000/docs
echo   DVWA           : http://localhost:4280
echo   Node API vuln. : http://localhost:3001
echo   SSH debil      : ssh labuser@localhost -p 2222  (pass: password123)
echo ----------------------------------------------------------------
echo   Para detener todo:  stop.bat
echo ================================================================
echo.
start "" "http://localhost:5173"
echo Abriendo el dashboard en tu navegador...
echo (Esta ventana se puede cerrar; los contenedores siguen corriendo.)
echo.
pause
endlocal
