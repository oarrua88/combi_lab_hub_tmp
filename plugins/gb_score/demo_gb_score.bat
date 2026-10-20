@echo off
chcp 65001 >nul
title CombiLabHUB - Demo GB-Score
echo ============================================================
echo   CombiLabHUB - Demo GB-Score (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\GB-Score.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"
set "MODEL=%SF%\GB_Score_figshare\gb_score.joblib"

if not exist "%SF%\GB_Score_figshare" mkdir "%SF%\GB_Score_figshare"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "gb-score" (Python 3.8.8 + scikit-learn 0.24.1)...
call conda env list | findstr /b /c:"gb-score " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda unos minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate gb-score
python -c "import sklearn, pandas, numpy; print('  sklearn', sklearn.__version__, '| pandas', pandas.__version__, '| numpy', numpy.__version__)"

echo.
echo [Paso 3/4] Codigo de GB-Score y modelo entrenado...
if not exist "%SF%\GB_Score\generate_features.py" (
  echo   Descomprimiendo GB-Score.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\GB_Score-HEAD" ren "%SF%\GB_Score-HEAD" GB_Score
)
if not exist "%SF%\GB_Score\generate_features.py" ( echo ERROR: no se encontro el codigo en %SF%\GB_Score & goto fin )
echo   Codigo OK: %SF%\GB_Score

if not exist "%MODEL%" (
  echo   Descargando gb_score.joblib desde Figshare ^(620 MB, unos minutos^)...
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://ndownloader.figshare.com/files/31280212' -OutFile '%MODEL%'"
)
if exist "%MODEL%" (
  echo   Verificando MD5 ^(debe ser 90ce46593c302792086ed402ebf93921^):
  certutil -hashfile "%MODEL%" MD5 | findstr /v "CertUtil"
) else (
  echo   AVISO: no se pudo descargar el modelo. Se prueban solo las features.
)

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
if exist "%MODEL%" (
  python "%PLUGIN%\test_1a30.py" --gb-dir "%SF%\GB_Score" --complex "%CASF%\coreset\1a30" --model "%MODEL%"
) else (
  python "%PLUGIN%\test_1a30.py" --gb-dir "%SF%\GB_Score" --complex "%CASF%\coreset\1a30"
)
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
