@echo off
chcp 65001 >nul
title CombiLabHUB - Demo T-ALPHA (Docker)
echo ============================================================
echo   CombiLabHUB - Demo T-ALPHA (complejo 1a30 de CASF-2016)
echo ============================================================
echo.
echo   T-ALPHA usa pykeops, que compila codigo C++ al ejecutarse y no tiene
echo   soporte oficial en Windows. En Windows se ejecuta dentro de Docker Desktop.
echo.
set "NOPAUSE=1"
call "%~dp0docker_t_alpha.bat"
set "NOPAUSE="
echo.
echo Listo. Presiona una tecla para cerrar esta ventana.
pause >nul
