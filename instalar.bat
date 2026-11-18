@echo off
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
echo Instalacion completada. Edita config.py y ejecuta iniciar.bat.
pause
exit /b 0
:error
echo No se pudo instalar. Instala Python 3.12.0 y su lanzador py.
pause
exit /b 1
