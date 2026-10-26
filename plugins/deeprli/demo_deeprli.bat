@echo off
chcp 65001 >nul
title CombiLabHUB - Demo DeepRLI
echo ============================================================
echo   CombiLabHUB - Demo DeepRLI (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"
set "COMMIT=9d6e73993edded01de57b765da42fe58463c670a"
set "MODEL_URL=https://github.com/fairydance/DeepRLI/releases/download/v1.0.2/trained_model.state_dict.pth"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "deeprli" (Python 3.10 + PyTorch 2.2 CPU + DGL 2.2.1 + RDKit 2023.09)...
call conda env list | findstr /b /c:"deeprli " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate deeprli
set "DGLBACKEND=pytorch"
python -W ignore -c "import torch, dgl, rdkit; print('  torch', torch.__version__, '| dgl', dgl.__version__, '| rdkit', rdkit.__version__)"

echo.
echo [Paso 3/4] Codigo de DeepRLI ^(commit fijado^) y modelo entrenado ^(release v1.0.2^)...
if not exist "%SF%\DeepRLI\src\deeprli" (
  echo   Descargando el codigo de GitHub...
  curl -L -o "%SF%\DeepRLI.zip" "https://github.com/fairydance/DeepRLI/archive/%COMMIT%.zip"
  if errorlevel 1 ( echo ERROR al descargar el codigo & goto fin )
  tar -xf "%SF%\DeepRLI.zip" -C "%SF%"
  ren "%SF%\DeepRLI-%COMMIT%" DeepRLI
  del "%SF%\DeepRLI.zip"
)
if not exist "%SF%\DeepRLI\src\deeprli" ( echo ERROR: no se encontro el codigo en %SF%\DeepRLI & goto fin )
echo   Codigo OK: %SF%\DeepRLI
if not exist "%SF%\DeepRLI\trained_model.state_dict.pth" (
  echo   Descargando el modelo entrenado ^(2.4 MB^)...
  curl -L -o "%SF%\DeepRLI\trained_model.state_dict.pth" "%MODEL_URL%"
  if errorlevel 1 ( echo ERROR al descargar el modelo & goto fin )
)
echo   Verificando MD5 del modelo ^(debe ser 334ada642693c0f68a8b0305e77f0a29^):
certutil -hashfile "%SF%\DeepRLI\trained_model.state_dict.pth" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --deeprli-dir "%SF%\DeepRLI" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
