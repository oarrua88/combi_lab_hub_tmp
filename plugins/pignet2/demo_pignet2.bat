@echo off
chcp 65001 >nul
title CombiLabHUB - Demo PIGNet2
echo ============================================================
echo   CombiLabHUB - Demo PIGNet2 (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\PIGNet2.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "pignet2" (Python 3.9 + PyTorch 2.2 CPU + PyG 2.0.3 + RDKit 2022.03 + PyMOL)...
call conda env list | findstr /b /c:"pignet2 " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate pignet2
python -W ignore -c "import torch, torch_geometric, torch_scatter, rdkit, pymol; print('  torch', torch.__version__, '| pyg', torch_geometric.__version__, '| rdkit', rdkit.__version__)"

echo.
echo [Paso 3/4] Codigo de PIGNet2 y modelos entrenados ^(vienen en el repositorio^)...
if not exist "%SF%\PIGNet2\src\ckpt\pda_0.pt" (
  echo   Descomprimiendo PIGNet2.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\PIGNet2-HEAD" ren "%SF%\PIGNet2-HEAD" PIGNet2
)
if not exist "%SF%\PIGNet2\src\ckpt\pda_0.pt" ( echo ERROR: no se encontro el codigo en %SF%\PIGNet2 & goto fin )
echo   Codigo OK: %SF%\PIGNet2
echo   Verificando MD5 del modelo pda_0 ^(debe ser 5d0f378dc68caee224502348513b6f8f^):
certutil -hashfile "%SF%\PIGNet2\src\ckpt\pda_0.pt" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python -W ignore "%PLUGIN%\test_1a30.py" --pignet2-dir "%SF%\PIGNet2" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
