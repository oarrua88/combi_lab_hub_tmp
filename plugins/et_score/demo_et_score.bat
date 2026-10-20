@echo off
chcp 65001 >nul
title CombiLabHUB - Demo ET-Score
echo ============================================================
echo   CombiLabHUB - Demo ET-Score (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\ET-Score.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "et-score" (Python 3.7 + scikit-learn 0.22.2)...
call conda env list | findstr /b /c:"et-score " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda unos minutos ^(~185 MB^)...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate et-score
python -c "import sklearn, pandas, numpy; print('  sklearn', sklearn.__version__, '| pandas', pandas.__version__, '| numpy', numpy.__version__)"

echo.
echo [Paso 3/4] Codigo de ET-Score y modelo entrenado...
if not exist "%SF%\ET_Score\predict.py" (
  echo   Descomprimiendo ET-Score.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\ET_Score-HEAD" ren "%SF%\ET_Score-HEAD" ET_Score
)
if not exist "%SF%\ET_Score\predict.py" ( echo ERROR: no se encontro el codigo en %SF%\ET_Score & goto fin )
echo   Codigo OK: %SF%\ET_Score

if not exist "%SF%\ET_Score\et_score.sav" (
  echo   Descargando et_score.sav desde Figshare ^(150 MB^)...
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; $f=(Invoke-RestMethod 'https://api.figshare.com/v2/articles/23684538/files') | Where-Object { $_.name -eq 'et_score.sav' }; Invoke-WebRequest -Uri $f.download_url -OutFile '%SF%\ET_Score\et_score.sav'"
)
if exist "%SF%\ET_Score\et_score.sav" (
  echo   Verificando MD5 ^(debe ser c7c5865d085fee31ed6e978c9b66c39e^):
  certutil -hashfile "%SF%\ET_Score\et_score.sav" MD5 | findstr /v "CertUtil"
  set "MODEL=--model %SF%\ET_Score\et_score.sav"
) else (
  echo   AVISO: no se pudo descargar el modelo. Se prueban solo las features.
  set "MODEL="
)

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
if defined MODEL (
  python "%PLUGIN%\test_1a30.py" --et-dir "%SF%\ET_Score" --complex "%CASF%\coreset\1a30" --model "%SF%\ET_Score\et_score.sav"
) else (
  python "%PLUGIN%\test_1a30.py" --et-dir "%SF%\ET_Score" --complex "%CASF%\coreset\1a30"
)
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
