@echo off
chcp 65001 >nul
title CombiLabHUB - Demo delta_LinF9_XGB (Docker)
echo ============================================================
echo   CombiLabHUB - Demo delta_LinF9_XGB (complejo 1a30 de CASF-2016)
echo ============================================================
echo.
echo   delta_LinF9_XGB usa programas que solo existen para Linux (smina, MSMS,
echo   MGLTools). En Windows se ejecuta dentro de Docker Desktop.
echo.

rem Rutas: PLUGIN es esta carpeta. CASF se puede definir antes de ejecutar.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
set "IMAGE=combilab/delta_linf9_xgb:1.0"

echo [Paso 1/3] Verificando Docker...
docker version >nul 2>&1
if errorlevel 1 ( echo ERROR: Docker no responde. Abri Docker Desktop y volve a ejecutar. & goto fin )
echo   Docker OK.

echo.
echo [Paso 2/3] Imagen %IMAGE%...
docker image inspect %IMAGE% >nul 2>&1
if errorlevel 1 (
  echo   Construyendo la imagen, tarda varios minutos la primera vez...
  docker build -t %IMAGE% "%PLUGIN%"
  if errorlevel 1 ( echo ERROR al construir la imagen & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)

echo.
echo [Paso 3/3] Test con el ejemplo de los autores ^(1e66^) y el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
docker run --rm -v "%CASF%\coreset\1a30:/complex:ro" %IMAGE% python -W ignore /opt/delta_linf9_xgb/test_1a30.py --dl-dir /opt/delta_LinF9_XGB --complex /complex
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
