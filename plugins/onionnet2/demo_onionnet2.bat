@echo off
chcp 65001 >nul
title CombiLabHUB - Demo OnionNet-2
echo ============================================================
echo   CombiLabHUB - Demo OnionNet-2 (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "TF_CPP_MIN_LOG_LEVEL=2"
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\OnionNet-2.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"
set "MODEL=%SF%\OnionNet-2\models\62shell_saved-model.h5"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "onionnet2" (Python 3.8 + TensorFlow 2.3 CPU + Open Babel)...
call conda env list | findstr /b /c:"onionnet2 " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda unos minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate onionnet2
python -c "import os; os.environ['TF_CPP_MIN_LOG_LEVEL']='3'; import tensorflow as tf, sklearn, numpy; print('  tensorflow', tf.__version__, '| sklearn', sklearn.__version__, '| numpy', numpy.__version__)"

echo.
echo [Paso 3/4] Codigo de OnionNet-2 y modelo entrenado...
if not exist "%SF%\OnionNet-2\scoring\predict.py" (
  echo   Descomprimiendo OnionNet-2.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\OnionNet-2-HEAD" ren "%SF%\OnionNet-2-HEAD" OnionNet-2
)
if not exist "%SF%\OnionNet-2\scoring\predict.py" ( echo ERROR: no se encontro el codigo en %SF%\OnionNet-2 & goto fin )
echo   Codigo OK: %SF%\OnionNet-2

if not exist "%MODEL%" (
  echo   Descargando 62shell_saved-model.h5 desde Zenodo ^(885 MB, unos minutos^)...
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://zenodo.org/records/10728089/files/62shell_saved-model.h5?download=1' -OutFile '%MODEL%'"
)
if exist "%MODEL%" (
  echo   Verificando MD5 ^(debe ser 52eb7563a867b5ee22f505070922cc6c^):
  certutil -hashfile "%MODEL%" MD5 | findstr /v "CertUtil"
) else (
  echo   AVISO: no se pudo descargar el modelo. Se prueban solo las features.
)

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
if exist "%MODEL%" (
  python "%PLUGIN%\test_1a30.py" --on-dir "%SF%\OnionNet-2" --complex "%CASF%\coreset\1a30" --model "%MODEL%"
) else (
  python "%PLUGIN%\test_1a30.py" --on-dir "%SF%\OnionNet-2" --complex "%CASF%\coreset\1a30"
)
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
