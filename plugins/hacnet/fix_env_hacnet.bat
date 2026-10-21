@echo off
chcp 65001 >nul
title CombiLabHUB - Reparar entorno hacnet
echo ============================================================
echo   Reparar el entorno conda "hacnet" (error libintl_dgettext)
echo ============================================================
echo.
echo   Problema: libglib 2.88.3 del canal "defaults" pisa intl-8.dll y PyMOL
echo   no arranca ("No se encuentra el punto de entrada ... libintl_dgettext").
echo   Solucion: glib 2.86.4 de conda-forge y reinstalar libintl.
echo.
if not defined CONDA set "CONDA=%USERPROFILE%\miniconda3"
call "%CONDA%\Scripts\activate.bat" "%CONDA%"
if errorlevel 1 ( echo ERROR: no se pudo activar Miniconda & goto fin )

echo [1/3] glib 2.86.4 desde conda-forge...
call conda install -y -n hacnet -c conda-forge --override-channels "libglib=2.86.4" "glib=2.86.4" "glib-tools=2.86.4"
if errorlevel 1 ( echo ERROR en el paso 1 & goto fin )

echo.
echo [2/3] Reinstalando libintl ^(restaura intl-8.dll^)...
call conda install -y -n hacnet -c conda-forge --override-channels --force-reinstall "libintl=0.22.5"
if errorlevel 1 ( echo ERROR en el paso 2 & goto fin )

echo.
echo [3/3] Probando PyMOL...
call conda activate hacnet
python -c "from pymol import cmd; print('  PyMOL OK', cmd.get_version()[0])"

:fin
echo.
echo Listo. Ahora volve a ejecutar demo_hacnet.bat. Presiona una tecla para cerrar.
pause >nul
