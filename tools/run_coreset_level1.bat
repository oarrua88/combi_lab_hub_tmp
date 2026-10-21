@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title CombiLabHUB - Core set CASF-2016 (Nivel 1)
echo ============================================================
echo   CombiLabHUB - Prediccion del core set de CASF-2016 (285)
echo   con las 10 scoring functions del Nivel 1 + calculo del PCC
echo ============================================================
echo.
rem Uso:
rem   run_coreset_level1.bat                  corre las 10 SF
rem   run_coreset_level1.bat gb sfcnn planet  corre solo esas
rem   Nombres: et gb onionnet2 sfcnn planet eggnn gign ehign_pla sacnn deattentiondta
rem Si una SF ya tiene results_<sf>\predictions.csv completo, se salta.
rem Para repetirla, borra esa carpeta o pon FORCE=1 antes de ejecutar.
rem Cada SF deja su log en results_<sf>\log.txt.

set "TOOLS=%~dp0"
if "%TOOLS:~-1%"=="\" set "TOOLS=%TOOLS:~0,-1%"
for %%i in ("%TOOLS%\..") do set "REPO=%%~fi"
set "PLUGINS=%REPO%\plugins"
if not defined SF set "SF=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\sf"
if not defined CASF set "CASF=C:\Users\Admin\Desktop\SOFTWARE SF\CASF-2016\CASF-2016"
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"
set "CORE=%CASF%\coreset"

if "%~1"=="" (
  for %%s in (et gb onionnet2 sfcnn planet eggnn gign ehign_pla sacnn deattentiondta) do set "RUN_%%s=1"
) else (
  for %%s in (%*) do set "RUN_%%s=1"
)

call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda en %CONDA% & goto fin )
if not exist "%CORE%\1a30" ( echo ERROR: no se encontro el core set en %CORE% & goto fin )

set "SUMMARY=%SF%\resultados_casf2016"
if not exist "%SUMMARY%" mkdir "%SUMMARY%"
set "TIMES=%SUMMARY%\tiempos.txt"
echo Corrida %DATE% %TIME% >> "%TIMES%"

rem ---------------------------------------------------------------- ET-Score
if defined RUN_et (
  call :begin et et-score et_score || goto next_et
  if not exist "%SF%\coreset_et\1a30" python "%PLUGINS%\et_score\prepare_casf.py" "%CORE%" "%SF%\coreset_et" >> "!LOG!" 2>&1
  pushd "%SF%\results_et"
  python "%SF%\ET_Score\predict.py" -m "%SF%\ET_Score\et_score.sav" -d "%SF%\coreset_et" >> "!LOG!" 2>&1
  python -c "import pandas as pd; d=pd.read_excel('prediction.xlsx', index_col=0); d.index=[str(i).strip()[-4:].lower() for i in d.index]; d.index.name='pdbid'; d.columns=['pKd_predicted']; d.to_csv('predictions.csv')" >> "!LOG!" 2>&1
  popd
  call :end et
)
:next_et

rem ---------------------------------------------------------------- GB-Score
if defined RUN_gb (
  call :begin gb gb-score gb_score || goto next_gb
  if not exist "%SF%\coreset_gb\1a30" python "%PLUGINS%\gb_score\prepare_casf.py" "%CORE%" "%SF%\coreset_gb" >> "!LOG!" 2>&1
  python "%PLUGINS%\gb_score\predict_gb_score.py" --gb-dir "%SF%\GB_Score" -d "%SF%\coreset_gb" -m "%SF%\GB_Score_figshare\gb_score.joblib" -o "%SF%\results_gb\predictions.csv" >> "!LOG!" 2>&1
  call :end gb
)
:next_gb

rem ---------------------------------------------------------------- OnionNet-2
if defined RUN_onionnet2 (
  call :begin onionnet2 onionnet2 onionnet2 || goto next_on
  python "%PLUGINS%\onionnet2\predict_onionnet2.py" --on-dir "%SF%\OnionNet-2" -d "%CORE%" -m "%SF%\OnionNet-2\models\62shell_saved-model.h5" -o "%SF%\results_onionnet2\predictions.csv" >> "!LOG!" 2>&1
  call :end onionnet2
)
:next_on

rem ---------------------------------------------------------------- SFCNN
if defined RUN_sfcnn (
  call :begin sfcnn sfcnn sfcnn || goto next_sfcnn
  python "%PLUGINS%\sfcnn\predict_sfcnn.py" --sfcnn-dir "%SF%\Sfcnn" -d "%CORE%" -o "%SF%\results_sfcnn\predictions.csv" >> "!LOG!" 2>&1
  call :end sfcnn
)
:next_sfcnn

rem ---------------------------------------------------------------- PLANET
if defined RUN_planet (
  call :begin planet planet planet || goto next_planet
  if not exist "%SF%\PLANET\core" ( pushd "%SF%\PLANET" & tar -xjf core.tar.bz2 >> "!LOG!" 2>&1 & popd )
  python "%PLUGINS%\planet\predict_planet.py" --planet-dir "%SF%\PLANET" -d "%SF%\PLANET\core" -o "%SF%\results_planet\predictions.csv" >> "!LOG!" 2>&1
  call :end planet
)
:next_planet

rem ---------------------------------------------------------------- egGNN
if defined RUN_eggnn (
  call :begin eggnn eggnn eggnn || goto next_eggnn
  python "%PLUGINS%\eggnn\predict_eggnn.py" --eggnn-dir "%SF%\egGNN" -d "%CORE%" -o "%SF%\results_eggnn\predictions.csv" >> "!LOG!" 2>&1
  call :end eggnn
)
:next_eggnn

rem ---------------------------------------------------------------- GIGN
if defined RUN_gign (
  call :begin gign gign gign || goto next_gign
  python "%PLUGINS%\gign\predict_gign.py" --gign-dir "%SF%\GIGN" -d "%CORE%" -o "%SF%\results_gign\predictions.csv" >> "!LOG!" 2>&1
  call :end gign
)
:next_gign

rem ---------------------------------------------------------------- EHIGN-PLA
if defined RUN_ehign_pla (
  call :begin ehign_pla gign ehign_pla || goto next_ehign
  python "%PLUGINS%\ehign_pla\predict_ehign_pla.py" --ehign-dir "%SF%\EHIGN_PLA" -d "%CORE%" -o "%SF%\results_ehign_pla\predictions.csv" >> "!LOG!" 2>&1
  call :end ehign_pla
)
:next_ehign

rem ---------------------------------------------------------------- saCNN
if defined RUN_sacnn (
  call :begin sacnn sacnn sacnn || goto next_sacnn
  python "%PLUGINS%\sacnn\predict_sacnn.py" --sacnn-dir "%SF%\saCNN" -d "%CORE%" -o "%SF%\results_sacnn\predictions.csv" >> "!LOG!" 2>&1
  call :end sacnn
)
:next_sacnn

rem ---------------------------------------------------------------- DEAttentionDTA
if defined RUN_deattentiondta (
  call :begin deattentiondta deattentiondta deattentiondta || goto next_dea
  python "%PLUGINS%\deattentiondta\predict_deattentiondta.py" --dea-dir "%SF%\DEAttentionDTA" -d "%CORE%" -o "%SF%\results_deattentiondta\predictions.csv" >> "!LOG!" 2>&1
  call :end deattentiondta
)
:next_dea

rem ---------------------------------------------------------------- PCC
echo.
echo ============================================================
echo   Calculando PCC contra CoreSet.dat
echo ============================================================
call conda activate gb-score
python "%TOOLS%\evaluate_casf.py" --sf-dir "%SF%" --coreset-dat "%CASF%\power_scoring\CoreSet.dat" -o "%SUMMARY%"

:fin
echo.
echo Listo. Avisale a Claude y presiona una tecla para cerrar.
pause >nul
exit /b

rem ================================================================ helpers
rem :begin <short name> <conda env> <plugin folder>
:begin
set "NAME=%~1"
set "OUT=%SF%\results_%~1"
set "LOG=%SF%\results_%~1\log.txt"
if not exist "%OUT%" mkdir "%OUT%"
if not defined FORCE if exist "%OUT%\predictions.csv" (
  for /f %%n in ('find /c /v "" ^< "%OUT%\predictions.csv"') do if %%n GEQ 286 (
    echo [%~1] ya tiene predictions.csv completo, se salta.
    exit /b 1
  )
)
echo.
echo [%~1] entorno %~2 - inicio %TIME%
call conda env list | findstr /b /c:"%~2 " >nul
if errorlevel 1 (
  echo   Creando el entorno %~2 ^(tarda varios minutos^)...
  call conda env create -f "%PLUGINS%\%~3\environment.yml" >> "%LOG%" 2>&1
  if errorlevel 1 ( echo   ERROR al crear el entorno, ver %LOG% & exit /b 1 )
)
call conda activate %~2
echo ==== %DATE% %TIME% ==== >> "%LOG%"
set "T0=%TIME%"
exit /b 0

rem :end <short name>
:end
set "N=0"
if exist "%OUT%\predictions.csv" for /f %%n in ('find /c /v "" ^< "%OUT%\predictions.csv"') do set /a "N=%%n-1"
if %N% GTR 0 (
  echo   [%~1] OK: %N% complejos predichos - fin %TIME%
) else (
  echo   [%~1] FALLO: no hay predicciones, ver %LOG%
)
echo %~1  inicio %T0%  fin %TIME%  complejos %N% >> "%TIMES%"
call conda deactivate
exit /b 0
