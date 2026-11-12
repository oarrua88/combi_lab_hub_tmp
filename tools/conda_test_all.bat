@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title CombiLabHUB - Tests con Windows conda de todas las SF
rem Crea (si hace falta) el entorno conda de cada SF y corre su test con 1a30, una por una.
rem Uso:  conda_test_all.bat                 todas
rem       conda_test_all.bat igmodel conbap  solo esas (nombres de carpeta de plugins\)
rem Una SF pasa si su log tiene RESULT: PASS y ningun RESULT: FAIL (algunas corren dos tests).
rem Cada log queda en %LOGDIR%\<sf>.log y el resumen en %LOGDIR%\resumen.txt
set "TOOLS=%~dp0"
if "%TOOLS:~-1%"=="\" set "TOOLS=%TOOLS:~0,-1%"
for %%i in ("%TOOLS%\..") do set "REPO=%%~fi"
if not defined LOGDIR set "LOGDIR=C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\resultados_conda"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "LIST=%*"
if "%LIST%"=="" set "LIST=et_score gb_score onionnet2 sfcnn planet eggnn gign ehign_pla sacnn deattentiondta rfl_score igmodel conbap hacnet deepbindgcn graphscoredta pointnet pignet2 bapa deeprli mmpd_dta dtitr autodock_vina deltavinarf20"
set NOPAUSE=1
echo Resumen %DATE% %TIME% > "%LOGDIR%\resumen.txt"
for %%s in (%LIST%) do (
  echo.
  echo ===== %%s  ^(inicio !TIME!^) =====
  call "%REPO%\plugins\%%s\demo_%%s.bat" > "%LOGDIR%\%%s.log" 2>&1
  set "OK=1"
  findstr /c:"RESULT: PASS" "%LOGDIR%\%%s.log" >nul || set "OK=0"
  findstr /c:"RESULT: FAIL" "%LOGDIR%\%%s.log" >nul && set "OK=0"
  if "!OK!"=="0" (
    echo   %%s: FAIL ^(ver %LOGDIR%\%%s.log^)
    echo %%s  FAIL >> "%LOGDIR%\resumen.txt"
  ) else (
    echo   %%s: PASS
    echo %%s  PASS >> "%LOGDIR%\resumen.txt"
  )
)
echo.
echo ============================================================
type "%LOGDIR%\resumen.txt"
:fin
echo.
echo Listo. Presiona una tecla para cerrar.
pause >nul
