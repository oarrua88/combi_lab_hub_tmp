@echo off
chcp 65001 >nul
title CombiLabHUB - Demo IGModel
echo ============================================================
echo   CombiLabHUB - Demo IGModel (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\IGModel.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "igmodel" (Python 3.10 + PyTorch 2.2 CPU + DGL 2.2.1 + RDKit + Open Babel)...
call conda env list | findstr /b /c:"igmodel " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate igmodel
set DGLBACKEND=pytorch
python -W ignore -c "import torch, dgl, rdkit; print('  torch', torch.__version__, '| dgl', dgl.__version__, '| rdkit', rdkit.__version__)"

echo.
echo [Paso 3/4] Codigo de IGModel y modelo entrenado...
if not exist "%SF%\IGModel\scripts\scoring.py" (
  echo   Descomprimiendo IGModel.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\IGModel-HEAD" ren "%SF%\IGModel-HEAD" IGModel
)
if not exist "%SF%\IGModel\scripts\scoring.py" ( echo ERROR: no se encontro el codigo en %SF%\IGModel & goto fin )
echo   Codigo OK: %SF%\IGModel
echo   Verificando MD5 de saved_model.pth ^(debe ser f7f17e91249bed9c90b8a7201c4c2402^):
certutil -hashfile "%SF%\IGModel\models\saved_model.pth" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el ejemplo de los autores ^(1bcu^) y el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python -W ignore "%PLUGIN%\test_1a30.py" --ig-dir "%SF%\IGModel" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
