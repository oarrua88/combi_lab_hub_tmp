@echo off
chcp 65001 >nul
title CombiLabHUB - Demo BAPA
echo ============================================================
echo   CombiLabHUB - Demo BAPA (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\BAPA.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "bapa" (Python 3.6 + TensorFlow 1.12 CPU + Open Babel 2.4.1)...
call conda env list | findstr /b /c:"bapa " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate bapa
set "TF_CPP_MIN_LOG_LEVEL=2"
python -W ignore -c "import tensorflow as tf, numpy; print('  tensorflow', tf.__version__, '| numpy', numpy.__version__)"
obabel -V

echo.
echo [Paso 3/4] Codigo de BAPA y red entrenada ^(vienen en el repositorio^)...
if not exist "%SF%\BAPA\module\network\BAPA_network.meta" (
  echo   Descomprimiendo BAPA.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\BAPA-HEAD" ren "%SF%\BAPA-HEAD" BAPA
)
if not exist "%SF%\BAPA\module\network\BAPA_network.meta" ( echo ERROR: no se encontro el codigo en %SF%\BAPA & goto fin )
echo   Codigo OK: %SF%\BAPA
echo   Verificando MD5 de la red ^(debe ser 8f33149ef5647678b837d76de4d07ccc^):
certutil -hashfile "%SF%\BAPA\module\network\BAPA_network.data-00000-of-00001" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python -W ignore "%PLUGIN%\test_1a30.py" --bapa-dir "%SF%\BAPA" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
