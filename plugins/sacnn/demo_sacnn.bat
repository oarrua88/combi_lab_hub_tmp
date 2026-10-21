@echo off
chcp 65001 >nul
title CombiLabHUB - Demo saCNN
echo ============================================================
echo   CombiLabHUB - Demo saCNN (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\saCNN.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "sacnn" (Python 3.10 + PyTorch 2.5 CPU + moleculekit 1.11.5)...
call conda env list | findstr /b /c:"sacnn " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate sacnn
python -W ignore -c "import torch, moleculekit, rdkit; print('  torch', torch.__version__, '| moleculekit', moleculekit.__version__, '| rdkit', rdkit.__version__)"

echo.
echo [Paso 3/4] Codigo de saCNN y modelo entrenado ^(vienen en el repositorio^)...
if not exist "%SF%\saCNN\src\model.py" (
  echo   Descomprimiendo saCNN.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\saCNN-HEAD" ren "%SF%\saCNN-HEAD" saCNN
)
if not exist "%SF%\saCNN\src\model.py" ( echo ERROR: no se encontro el codigo en %SF%\saCNN & goto fin )
echo   Codigo OK: %SF%\saCNN
echo   Verificando MD5 de model.pkl ^(debe ser 0418f265c1dc6758a4a76aae0ae7531c^):
certutil -hashfile "%SF%\saCNN\checkpoint\model.pkl" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --sacnn-dir "%SF%\saCNN" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
