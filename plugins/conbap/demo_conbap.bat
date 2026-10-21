@echo off
chcp 65001 >nul
title CombiLabHUB - Demo ConBAP
echo ============================================================
echo   CombiLabHUB - Demo ConBAP (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\ConBAP.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "conbap" (Python 3.10 + PyTorch 2.2 CPU + PyG + GVP + RDKit + PyMOL)...
call conda env list | findstr /b /c:"conbap " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate conbap
python -c "import gvp" 2>nul
if errorlevel 1 (
  echo   Instalando GVP-GNN ^(sin atom3d^)...
  pip install --no-deps "https://github.com/drorlab/gvp-pytorch/archive/316eea7cd6446dd928e5975634152ec3b28e65f5.zip"
)
python -W ignore -c "import torch, torch_geometric, torch_scatter, gvp, rdkit, pymol; print('  torch', torch.__version__, '| pyg', torch_geometric.__version__, '| rdkit', rdkit.__version__)"

echo.
echo [Paso 3/4] Codigo de ConBAP y modelo entrenado...
if not exist "%SF%\ConBAP\supervised\ConBAP.py" (
  echo   Descomprimiendo ConBAP.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\ConBAP-HEAD" ren "%SF%\ConBAP-HEAD" ConBAP
)
if not exist "%SF%\ConBAP\supervised\ConBAP.py" ( echo ERROR: no se encontro el codigo en %SF%\ConBAP & goto fin )
echo   Codigo OK: %SF%\ConBAP
echo   Verificando MD5 del modelo de afinidad ^(debe ser 0256bb84bdf87fb2f0671f0acbd33358^):
certutil -hashfile "%SF%\ConBAP\supervised\model\20231007_111336_ConBAP_repeat0\model\epoch-292, train_loss-0.1220, train_rmse-0.3493, valid_rmse-1.1663, valid_pr-0.7788.pt" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el ejemplo de los autores ^(1bcu^) y el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python -W ignore "%PLUGIN%\test_1a30.py" --conbap-dir "%SF%\ConBAP" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
