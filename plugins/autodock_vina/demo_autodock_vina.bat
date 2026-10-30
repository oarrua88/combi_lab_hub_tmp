@echo off
chcp 65001 >nul
title CombiLabHUB - Demo AutoDock Vina
echo ============================================================
echo   CombiLabHUB - Demo AutoDock Vina (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"
set "VINA_URL=https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_win.exe"
set "VINA=%SF%\AutoDock-Vina\vina_1.2.5_win.exe"

if not exist "%SF%\AutoDock-Vina" mkdir "%SF%\AutoDock-Vina"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "autodock_vina" (Python 3.10 + Open Babel 3.1.1)...
call conda env list | findstr /b /c:"autodock_vina " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda unos minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate autodock_vina
obabel -V

echo.
echo [Paso 3/4] Programa AutoDock Vina 1.2.5 ^(binario oficial para Windows^)...
if not exist "%VINA%" (
  echo   Descargando vina_1.2.5_win.exe ^(1.2 MB^)...
  curl -L -o "%VINA%" "%VINA_URL%"
  if errorlevel 1 ( echo ERROR al descargar Vina & goto fin )
)
echo   Verificando MD5 ^(debe ser 39ff27d9b1f29b4a8e7a1f35e3186861^):
certutil -hashfile "%VINA%" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --vina "%VINA%" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
