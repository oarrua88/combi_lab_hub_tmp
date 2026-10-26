@echo off
chcp 65001 >nul
title CombiLabHUB - Docker T-ALPHA
echo ============================================================
echo   CombiLabHUB - T-ALPHA con Docker (test con el complejo 1a30)
echo ============================================================
echo.
rem Construye la imagen combilab/t_alpha:1.0 (solo la primera vez) y corre el test dentro del contenedor.
rem La primera vez descarga unos 2,3 GB de Zenodo. Para reconstruir la imagen: set REBUILD=1 antes de ejecutar.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
set "IMAGE=combilab/t_alpha:1.0"

echo [Paso 1/3] Verificando Docker...
docker version >nul 2>&1
if errorlevel 1 ( echo ERROR: Docker no responde. Abri Docker Desktop y espera "Engine running". & goto fin )
echo   Docker OK.

echo.
echo [Paso 2/3] Imagen %IMAGE%...
if defined REBUILD docker image rm -f %IMAGE% >nul 2>&1
docker image inspect %IMAGE% >nul 2>&1
if errorlevel 1 (
  echo   Construyendo la imagen: descarga unos 2,3 GB y compila pykeops, tarda bastante la primera vez...
  docker build -t %IMAGE% "%PLUGIN%"
  if errorlevel 1 ( echo ERROR al construir la imagen & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)

echo.
echo [Paso 3/3] Test dentro del contenedor ^(1a30, proteasa HIV-1^)...
echo ------------------------------------------------------------
docker run --rm %IMAGE% python -W ignore /opt/t_alpha/test_1a30.py --talpha-dir /opt/T-ALPHA --data-dir /opt/talpha_data
echo ------------------------------------------------------------

:fin
echo.
if not defined NOPAUSE (
  echo Listo. Presiona una tecla para cerrar esta ventana.
  pause >nul
)
