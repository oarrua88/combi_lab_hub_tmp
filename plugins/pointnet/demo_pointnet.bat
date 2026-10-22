@echo off
chcp 65001 >nul
title CombiLabHUB - Demo PointNet / PointTransformer
echo ============================================================
echo   CombiLabHUB - Demo PointNet / PointTransformer (1a30)
echo ============================================================
echo.
rem En Windows se prueban los modelos con nubes de puntos ya armadas. El programa
rem POINTNET de los autores (arma la nube) es solo para Linux: usar docker_pointnet.bat.

rem Rutas: PLUGIN es esta carpeta. SF, CASF, ZIP y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined ZIP set "ZIP=C:\Users\Admin\Desktop\SOFTWARE SF\Funciones_Score_Tabla1\pointnet.zip"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "pointnet" (Python 3.10 + PyTorch 2.2 CPU)...
call conda env list | findstr /b /c:"pointnet " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda unos minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate pointnet
python -W ignore -c "import torch, numpy; print('  torch', torch.__version__, '| numpy', numpy.__version__)"

echo.
echo [Paso 3/4] Codigo y modelos entrenados ^(vienen en el repositorio, ~500 MB^)...
if not exist "%SF%\PointNet\pointmodel.py" (
  echo   Descomprimiendo pointnet.zip...
  tar -xf "%ZIP%" -C "%SF%"
  if exist "%SF%\Point-Cloud-HEAD" ren "%SF%\Point-Cloud-HEAD" PointNet
)
if not exist "%SF%\PointNet\pointmodel.py" ( echo ERROR: no se encontro el codigo en %SF%\PointNet & goto fin )
echo   Codigo OK: %SF%\PointNet
echo   Verificando MD5 del modelo PointTransformer 0.827 ^(debe ser 0dde813d2d3d2803145b21263041d19d^):
for %%F in ("%SF%\PointNet\Model\PointTransformer*\0.827.pth") do certutil -hashfile "%%~fF" MD5 | findstr /v "CertUtil"

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python -W ignore "%PLUGIN%\test_1a30.py" --pointnet-dir "%SF%\PointNet" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
