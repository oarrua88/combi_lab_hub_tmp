@echo off
chcp 65001 >nul
title CombiLabHUB - Demo DeepBindGCN
echo ============================================================
echo   CombiLabHUB - Demo DeepBindGCN (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\DeepBindGCN.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "deepbindgcn" (Python 3.10 + PyTorch 2.2 CPU + PyG 2.5.3 + RDKit)...
call conda env list | findstr /b /c:"deepbindgcn " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate deepbindgcn
python -W ignore -c "import torch, torch_geometric, rdkit; print('  torch', torch.__version__, '| pyg', torch_geometric.__version__, '| rdkit', rdkit.__version__)"

echo.
echo [Paso 3/4] Codigo de DeepBindGCN y modelo entrenado...
if not exist "%SF%\DeepBindGCN\DeepBindGCN_RG_example\models\gcn.py" (
  echo   Descomprimiendo DeepBindGCN.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\DeepBindGCN-HEAD" ren "%SF%\DeepBindGCN-HEAD" DeepBindGCN
)
if not exist "%SF%\DeepBindGCN\DeepBindGCN_RG_example\models\gcn.py" ( echo ERROR: no se encontro el codigo en %SF%\DeepBindGCN & goto fin )
echo   Codigo OK: %SF%\DeepBindGCN
set "MODEL=%SF%\DeepBindGCN\DeepBindGCN_RG_example\full_model_out2000_RG.model"
if not exist "%MODEL%" (
  echo   Descargando el modelo entrenado ^(34 MB, release v1.0.0 de GitHub^)...
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/haiping1010/DeepBindGCN/releases/download/v1.0.0/full_model_out2000_RG.model' -OutFile '%MODEL%'"
)
echo   Verificando MD5 ^(debe ser aaa694546e7cf41c9d2c3417df197d17^):
certutil -hashfile "%MODEL%" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python -W ignore "%PLUGIN%\test_1a30.py" --dbg-dir "%SF%\DeepBindGCN" --model "%MODEL%" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
