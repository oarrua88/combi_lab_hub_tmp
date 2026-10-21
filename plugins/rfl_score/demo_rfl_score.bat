@echo off
chcp 65001 >nul
title CombiLabHUB - Demo RFL-Score
echo ============================================================
echo   CombiLabHUB - Demo RFL-Score (test con el complejo 1a30)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\RFL-Score.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "rfl_score" (Python 3.10 + R 4.3 + randomForest)...
call conda env list | findstr /b /c:"rfl_score " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate rfl_score
python -c "import pandas; print('  pandas', pandas.__version__)"
python -c "import sys; sys.path.insert(0, r'%PLUGIN%'); import predict_rfl_score as W; print('  Rscript:', W.find_rscript())"

echo.
echo [Paso 3/4] Codigo de RFL-Score y modelo entrenado...
if not exist "%SF%\rfl-score_v1\scoring\RScript\model\scoring_function_160.rda" (
  echo   Descomprimiendo RFL-Score.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\rfl-score_v1-HEAD" ren "%SF%\rfl-score_v1-HEAD" rfl-score_v1
)
if not exist "%SF%\rfl-score_v1\scoring\RScript\model\scoring_function_160.rda" ( echo ERROR: no se encontro el codigo en %SF%\rfl-score_v1 & goto fin )
echo   Codigo OK: %SF%\rfl-score_v1
if not exist "%SF%\rfl-score_v1\examples\1a30\1a30_160_input.csv" ( echo ERROR: falta examples\1a30\1a30_160_input.csv & goto fin )
echo.
echo [Paso 4/4] Test: modelo Random Forest de los autores con las 160 features de 1a30 (el pipeline completo de features corre con Docker)
echo ------------------------------------------------------------
python -W ignore "%PLUGIN%\test_1a30.py" --rfl-dir "%SF%\rfl-score_v1"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
