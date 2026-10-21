@echo off
chcp 65001 >nul
title CombiLabHUB - Demo DEAttentionDTA
echo ============================================================
echo   CombiLabHUB - Demo DEAttentionDTA (complejo 1a30 de CASF-2016)
echo ============================================================
echo.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\DEAttentionDTA.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "deattentiondta" (Python 3.10 + PyTorch 2.2 CPU + Open Babel)...
call conda env list | findstr /b /c:"deattentiondta " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda varios minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate deattentiondta
python -c "import torch, numpy; from openbabel import pybel; print('  torch', torch.__version__, '| numpy', numpy.__version__, '| openbabel', pybel.ob.OBReleaseVersion())"

echo.
echo [Paso 3/4] Codigo de DEAttentionDTA y los 10 modelos entrenados ^(vienen en el repositorio^)...
if not exist "%SF%\DEAttentionDTA\src\bestmodel.py" (
  echo   Descomprimiendo DEAttentionDTA.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\DEAttentionDTA-HEAD" ren "%SF%\DEAttentionDTA-HEAD" DEAttentionDTA
)
if not exist "%SF%\DEAttentionDTA\src\bestmodel.py" ( echo ERROR: no se encontro el codigo en %SF%\DEAttentionDTA & goto fin )
echo   Codigo OK: %SF%\DEAttentionDTA
echo   Verificando MD5 de "Fold 1 best_model.ckpt" ^(debe ser 7c9ce530d8d8858752668d827bc31027^):
certutil -hashfile "%SF%\DEAttentionDTA\src\model\Fold 1 best_model.ckpt" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --dea-dir "%SF%\DEAttentionDTA" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
