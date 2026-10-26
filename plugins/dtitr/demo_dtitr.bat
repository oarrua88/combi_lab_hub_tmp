@echo off
chcp 65001 >nul
title CombiLabHUB - Demo DTITR
echo ============================================================
echo   CombiLabHUB - Demo DTITR (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"
set "COMMIT=e8d53619a5351bbc8ee992041c91bf014629aa89"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "dtitr" (Python 3.9 + TensorFlow 2.6 CPU + RDKit)...
call conda env list | findstr /b /c:"dtitr " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate dtitr
set TF_CPP_MIN_LOG_LEVEL=2
python -W ignore -c "import tensorflow as tf, tensorflow_addons, rdkit; print('  tensorflow', tf.__version__, '| rdkit', rdkit.__version__)"

echo.
echo [Paso 3/4] Codigo de DTITR ^(commit fijado; el modelo entrenado viene en el repositorio^)...
if not exist "%SF%\DTITR\source\dtitr_model.py" (
  echo   Descargando el codigo de GitHub ^(unos 80 MB^)...
  curl -L -o "%SF%\DTITR.zip" "https://github.com/larngroup/DTITR/archive/%COMMIT%.zip"
  if errorlevel 1 ( echo ERROR al descargar el codigo & goto fin )
  tar -xf "%SF%\DTITR.zip" -C "%SF%"
  ren "%SF%\DTITR-%COMMIT%" DTITR
  del "%SF%\DTITR.zip"
)
if not exist "%SF%\DTITR\source\dtitr_model.py" ( echo ERROR: no se encontro el codigo en %SF%\DTITR & goto fin )
echo   Codigo OK: %SF%\DTITR
echo   Verificando MD5 del modelo ^(debe ser 69c9aca0c415bb54c63a1c01c3a8da4e^):
certutil -hashfile "%SF%\DTITR\model\dtitr_model\.data-00000-of-00001" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^), tarda 1-2 minutos...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --dtitr-dir "%SF%\DTITR" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
