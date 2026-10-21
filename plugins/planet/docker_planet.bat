@echo off
chcp 65001 >nul
title CombiLabHUB - Docker PLANET
echo ============================================================
echo   CombiLabHUB - PLANET con Docker (test con el complejo 1a30)
echo ============================================================
echo.
rem Construye la imagen combilab/planet:1.0 (solo la primera vez) y corre el test dentro del contenedor.
rem Para reconstruir la imagen: set REBUILD=1 antes de ejecutar.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
set "IMAGE=combilab/planet:1.0"

echo [Paso 1/3] Verificando Docker...
docker version >nul 2>&1
if errorlevel 1 ( echo ERROR: Docker no responde. Abri Docker Desktop y espera "Engine running". & goto fin )
echo   Docker OK.

echo.
echo [Paso 2/3] Imagen %IMAGE%...
if defined REBUILD docker image rm -f %IMAGE% >nul 2>&1
docker image inspect %IMAGE% >nul 2>&1
if errorlevel 1 (
  echo   Construyendo la imagen, la primera vez tarda varios minutos...
  docker build -t %IMAGE% "%PLUGIN%"
  if errorlevel 1 ( echo ERROR al construir la imagen & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)

echo.
echo [Paso 3/3] Test dentro del contenedor...
echo ------------------------------------------------------------
if not exist "%CASF%\coreset\1a30" ( echo ERROR: no se encontro %CASF%\coreset\1a30 & goto fin )
docker run --rm -v "%CASF%\coreset\1a30:/complex:ro" %IMAGE% python /opt/planet/test_1a30.py --planet-dir /opt/PLANET --complex /complex
echo ------------------------------------------------------------

:fin
echo.
if not defined NOPAUSE (
  echo Listo. Presiona una tecla para cerrar esta ventana.
  pause >nul
)
