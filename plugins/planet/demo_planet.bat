@echo off
chcp 65001 >nul
title CombiLabHUB - Demo PLANET
echo ============================================================
echo   CombiLabHUB - Demo PLANET (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\PLANET.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "planet" (Python 3.11 + PyTorch 2.2 CPU + RDKit)...
call conda env list | findstr /b /c:"planet " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate planet
python -c "import torch, rdkit, numpy; print('  torch', torch.__version__, '| rdkit', rdkit.__version__, '| numpy', numpy.__version__)"

echo.
echo [Paso 3/4] Codigo de PLANET, parametros entrenados y core set preparado ^(vienen en el repositorio^)...
if not exist "%SF%\PLANET\PLANET_run.py" (
  echo   Descomprimiendo PLANET.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\PLANET-HEAD" ren "%SF%\PLANET-HEAD" PLANET
)
if not exist "%SF%\PLANET\PLANET_run.py" ( echo ERROR: no se encontro el codigo en %SF%\PLANET & goto fin )
echo   Codigo OK: %SF%\PLANET
echo   Verificando MD5 de PLANET.param ^(debe ser e9c74b412e99367865a1eeb9fbd95feb^):
certutil -hashfile "%SF%\PLANET\PLANET.param" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --planet-dir "%SF%\PLANET" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
