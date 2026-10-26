@echo off
chcp 65001 >nul
title CombiLabHUB - Demo MMPD-DTA
echo ============================================================
echo   CombiLabHUB - Demo MMPD-DTA (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"
set "COMMIT=69926361c8155fdd40ea2aef7df0aa3fd7de1353"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "mmpd_dta" (Python 3.10 + PyTorch 2.2 CPU + PyG 2.5.3 + RDKit 2023.09.6)...
call conda env list | findstr /b /c:"mmpd_dta " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate mmpd_dta
python -W ignore -c "import torch, torch_geometric, rdkit; print('  torch', torch.__version__, '| PyG', torch_geometric.__version__, '| rdkit', rdkit.__version__)"

echo.
echo [Paso 3/4] Codigo de MMPD-DTA ^(commit fijado; el modelo entrenado viene en el repositorio^)...
if not exist "%SF%\MMPD-DTA\model.py" (
  echo   Descargando el codigo de GitHub ^(unos 22 MB^)...
  curl -L -o "%SF%\MMPD-DTA.zip" "https://github.com/zhc-moushang/MMPD-DTA/archive/%COMMIT%.zip"
  if errorlevel 1 ( echo ERROR al descargar el codigo & goto fin )
  tar -xf "%SF%\MMPD-DTA.zip" -C "%SF%"
  ren "%SF%\MMPD-DTA-%COMMIT%" MMPD-DTA
  del "%SF%\MMPD-DTA.zip"
)
if not exist "%SF%\MMPD-DTA\model.py" ( echo ERROR: no se encontro el codigo en %SF%\MMPD-DTA & goto fin )
echo   Codigo OK: %SF%\MMPD-DTA
if not exist "%SF%\MMPD-DTA\data\processed\test2016.pt" (
  echo   Extrayendo test2016.pt de data.zip ^(grafos de los autores, para comparar^)...
  tar -xf "%SF%\MMPD-DTA\data\processed\data.zip" -C "%SF%\MMPD-DTA\data\processed" test2016.pt
)
echo   Verificando MD5 del modelo ^(debe ser 366d95ccc2f7fdf87ae70746cb03ce39^):
certutil -hashfile "%SF%\MMPD-DTA\result\best\best_model.pt" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --mmpd-dir "%SF%\MMPD-DTA" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
