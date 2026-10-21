@echo off
chcp 65001 >nul
title CombiLabHUB - Demo HAC-Net
echo ============================================================
echo   CombiLabHUB - Demo HAC-Net (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\HAC-Net.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "hacnet" (Python 3.10 + PyTorch 2.2 CPU + PyG + Open Babel + PyMOL + HACNet 1.4.3)...
call conda env list | findstr /b /c:"hacnet " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate hacnet
python -W ignore -c "import torch, torch_geometric, openbabel, pymol; from importlib.metadata import version; print('  torch', torch.__version__, '| pyg', torch_geometric.__version__, '| HACNet', version('HACNet'))"

echo.
echo [Paso 3/4] Codigo de HAC-Net y modelo entrenado...
if not exist "%SF%\HAC-Net\HACNet\parameter_files\CNN_parameters.pt" (
  echo   Descomprimiendo HAC-Net.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\HAC-Net-HEAD" ren "%SF%\HAC-Net-HEAD" HAC-Net
)
if not exist "%SF%\HAC-Net\HACNet\parameter_files\CNN_parameters.pt" ( echo ERROR: no se encontro el codigo en %SF%\HAC-Net & goto fin )
echo   Codigo OK: %SF%\HAC-Net
echo   Verificando MD5 de CNN_parameters.pt ^(debe ser 7a16badb6abcdbf9075aea5f69b5acdf^):
certutil -hashfile "%SF%\HAC-Net\HACNet\parameter_files\CNN_parameters.pt" MD5 | findstr /v "CertUtil"
echo   Las cargas del pocket se calculan en el servidor ACC2 ^(se necesita internet^).

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python -W ignore "%PLUGIN%\test_1a30.py" --hacnet-dir "%SF%\HAC-Net" --complex "%CASF%\coreset\1a30" --charges acc2
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
