@echo off
chcp 65001 >nul
title CombiLabHUB - Demo GraphscoreDTA
echo ============================================================
echo   CombiLabHUB - Demo GraphscoreDTA (modelo de los autores sobre CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\GraphScoreDTA.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "gsdta" (Python 3.10 + PyTorch 2.2 CPU + DGL 2.2.1)...
call conda env list | findstr /b /c:"gsdta " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate gsdta
set DGLBACKEND=pytorch
python -W ignore -c "import torch, dgl; print('  torch', torch.__version__, '| dgl', dgl.__version__)"

echo.
echo [Paso 3/4] Codigo de GraphscoreDTA y modelo entrenado...
if not exist "%SF%\GraphscoreDTA\src\model.py" (
  echo   Descomprimiendo GraphScoreDTA.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\GraphscoreDTA-HEAD" ren "%SF%\GraphscoreDTA-HEAD" GraphscoreDTA
)
if not exist "%SF%\GraphscoreDTA\src\model.py" ( echo ERROR: no se encontro el codigo en %SF%\GraphscoreDTA & goto fin )
echo   Codigo OK: %SF%\GraphscoreDTA
set "BIN=%SF%\GraphscoreDTA\test_set\all_in_one_graph_test2016.bin"
if not exist "%BIN%" (
  echo   Descargando los grafos de CASF-2016 preparados por los autores ^(35 MB^)...
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/CSUBioGroup/GraphscoreDTA/releases/download/Data/all_in_one_graph_test2016.bin' -OutFile '%BIN%'"
)
echo   Verificando MD5 ^(debe ser a8c2ad64c46c2f13a6702a0856bde044^):
certutil -hashfile "%BIN%" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test: 1a30 no esta en los datos de los autores; se reproducen sus 279 predicciones...
echo ------------------------------------------------------------
python -W ignore "%PLUGIN%\test_1a30.py" --gs-dir "%SF%\GraphscoreDTA"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
