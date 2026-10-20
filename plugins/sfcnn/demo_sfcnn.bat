@echo off
chcp 65001 >nul
title CombiLabHUB - Demo Sfcnn
echo ============================================================
echo   CombiLabHUB - Demo Sfcnn (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "TF_CPP_MIN_LOG_LEVEL=2"
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\SFCNN.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "sfcnn" (Python 3.8 + TensorFlow 2.3 CPU + Open Babel)...
call conda env list | findstr /b /c:"sfcnn " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate sfcnn
python -c "import os; os.environ['TF_CPP_MIN_LOG_LEVEL']='3'; import tensorflow as tf, numpy; from openbabel import openbabel as ob; print('  tensorflow', tf.__version__, '| numpy', numpy.__version__, '| openbabel', ob.OBReleaseVersion())"

echo.
echo [Paso 3/4] Codigo de Sfcnn y pesos entrenados ^(vienen en el repositorio^)...
if not exist "%SF%\Sfcnn\predict.py" (
  echo   Descomprimiendo SFCNN.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\Sfcnn-HEAD" ren "%SF%\Sfcnn-HEAD" Sfcnn
)
if not exist "%SF%\Sfcnn\predict.py" ( echo ERROR: no se encontro el codigo en %SF%\Sfcnn & goto fin )
echo   Codigo OK: %SF%\Sfcnn
echo   Verificando MD5 de los pesos ^(debe ser b1315396dfd1616b4be80fdaeff4a428^):
certutil -hashfile "%SF%\Sfcnn\weights_22_112-0.0083.h5" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^) y sus 74 poses de docking...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --sfcnn-dir "%SF%\Sfcnn" --complex "%CASF%\coreset\1a30" --decoys
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
