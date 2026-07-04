@echo off
setlocal
title CyberSim - Stop
cd /d "%~dp0"

echo ================================================================
echo   Deteniendo CyberSim...
echo ================================================================
echo.

docker compose version >nul 2>&1
if errorlevel 1 (
    set "COMPOSE=docker-compose"
) else (
    set "COMPOSE=docker compose"
)

REM Detener y eliminar contenedores + red. Los volumenes (historial en
REM PostgreSQL) se conservan. Para borrar tambien la BD usa: stop.bat --wipe
if /i "%~1"=="--wipe" (
    echo Eliminando contenedores Y datos (volumenes)...
    %COMPOSE% down -v
) else (
    %COMPOSE% down
)

echo.
echo CyberSim detenido.
echo ^(Para borrar tambien el historial de la BD: stop.bat --wipe^)
echo.
pause
endlocal
