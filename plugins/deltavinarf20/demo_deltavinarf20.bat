@echo off
chcp 65001 >nul
title CombiLabHUB - Demo DeltaVinaRF20
echo ============================================================
echo   CombiLabHUB - Demo DeltaVinaRF20 (complejo 1a30 de CASF-2016)
echo ============================================================
echo.
rem En Windows se prueba el modelo entrenado (R + randomForest) con el ejemplo de los autores y con
rem las features de 1a30 guardadas en features_1a30.csv. El calculo de las features (codigo Python 2,
rem MGLTools, vina4dv, MSMS) es solo Linux: para eso usar docker_deltavinarf20.bat.

rem Rutas: PLUGIN es esta carpeta. SF, CASF y CONDA se pueden definir antes de ejecutar;
rem si no, se usan los valores de la computadora del laboratorio.
set "PLUGIN=%~dp0"
if "%PLUGIN:~-1%"=="\" set "PLUGIN=%PLUGIN:~0,-1%"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"
set "COMMIT=612bbe7f8b854a583ab81f4f1357422b0c108c98"

if not exist "%SF%" mkdir "%SF%"

echo [Paso 1/4] Activando Miniconda...
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo.
echo [Paso 2/4] Entorno conda "deltavinarf20_win" (Python 3.10 + R 4.3.3 + randomForest 4.7-1.2)...
call conda env list | findstr /b /c:"deltavinarf20_win " >nul
if errorlevel 1 (
  echo   Creando el entorno, tarda unos minutos...
  call conda env create -f "%PLUGIN%\environment.yml"
  if errorlevel 1 ( echo ERROR al crear el entorno & goto fin )
) else (
  echo   Ya existe, se reutiliza.
)
call conda activate deltavinarf20_win

echo.
echo [Paso 3/4] Codigo de deltavina ^(commit fijado, incluye el modelo rffit.rda^)...
if not exist "%SF%\deltavina\deltavina\models\rffit.rda" (
  echo   Descargando el codigo de GitHub...
  curl -L -o "%SF%\deltavina.zip" "https://github.com/chengwang88/deltavina/archive/%COMMIT%.zip"
  if errorlevel 1 ( echo ERROR al descargar el codigo & goto fin )
  tar -xf "%SF%\deltavina.zip" -C "%SF%"
  ren "%SF%\deltavina-%COMMIT%" deltavina
  del "%SF%\deltavina.zip"
)
if not exist "%SF%\deltavina\deltavina\models\rffit.rda" ( echo ERROR: no se encontro el modelo en %SF%\deltavina & goto fin )
echo   Codigo OK: %SF%\deltavina

echo.
echo [Paso 4/4] Test con el complejo 1a30 ^(proteasa HIV-1^)...
echo ------------------------------------------------------------
python "%PLUGIN%\test_1a30.py" --dv-dir "%SF%\deltavina" --complex "%CASF%\coreset\1a30"
echo ------------------------------------------------------------

:fin
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
