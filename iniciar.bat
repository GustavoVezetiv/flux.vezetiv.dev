@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado.
  echo Execute instalar.bat primeiro.
  pause
  exit /b 1
)

echo Iniciando IMOBI Automation...
".venv\Scripts\python.exe" -m streamlit run app.py

if errorlevel 1 (
  echo.
  echo O aplicativo encerrou com erro.
  pause
)
