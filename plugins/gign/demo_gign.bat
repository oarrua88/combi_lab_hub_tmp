@echo off
chcp 65001 >nul
title CombiLabHUB - Demo GIGN
echo ============================================================
echo   CombiLabHUB - Demo GIGN (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\GIGN.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "gign" (compartido por GIGN y EHIGN-PLA: PyTorch 2.2 CPU + PyG + DGL + RDKit + PyMOL + Open Babel)...
call conda env list | findstr /b /c:"gign " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate gign
set "DGLBACKEND=pytorch"
python -W ignore -c "import torch, torch_geometric, dgl, rdkit, pymol; print('  torch', torch.__version__, '| pyg', torch_geometric.__version__, '| dgl', dgl.__version__, '| rdkit', rdkit.__version__)"
obabel -V

echo.
echo [Paso 3/4] Codigo de GIGN y modelos entrenados ^(vienen en el repositorio^)...
if not exist "%SF%\GIGN\GIGN\GIGN.py" (
  echo   Descomprimiendo GIGN.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\GIGN-HEAD" ren "%SF%\GIGN-HEAD" GIGN
)
if not exist "%SF%\GIGN\GIGN\GIGN.py" ( echo ERROR: no se encontro el codigo en %SF%\GIGN & goto fin )
echo   Codigo OK: %SF%\GIGN
echo   Verificando MD5 del modelo 0 ^(debe ser b50f62d129b36c7ae2b4c22f214f2e57^):
for %%F in ("%SF%\GIGN\GIGN\model\20221121_074758_GIGN_repeat0\model\epoch-532*.pt") do certutil -hashfile "%%~fF" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --gign-dir "%SF%\GIGN" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
