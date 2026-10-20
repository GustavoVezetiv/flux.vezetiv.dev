@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================
echo   IMOBI Automation - Instalacao
 echo ==========================================

echo.
set "PYTHON_EXE="

REM Preferir instalacoes reais do Python no Windows.
for %%V in (313 312 311) do (
  if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python%%V\python.exe"
  )
)

REM Fallback para python.exe do PATH.
if not defined PYTHON_EXE (
  for /f "delims=" %%P in ('where python.exe 2^>nul') do (
    if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
  )
)

if not defined PYTHON_EXE (
  echo ERRO: Nao encontrei uma instalacao valida do Python 3.11+.
  echo Instale Python 3.11, 3.12 ou 3.13 e tente novamente.
  pause
  exit /b 1
)

echo Python selecionado:
echo   %PYTHON_EXE%
"%PYTHON_EXE%" --version
if errorlevel 1 (
  echo ERRO: O Python encontrado nao conseguiu iniciar.
  pause
  exit /b 1
)

echo.
REM Se houve tentativa anterior quebrada, limpar apenas o .venv incompleto.
if exist ".venv" if not exist ".venv\Scripts\python.exe" (
  echo Removendo ambiente virtual incompleto...
  rmdir /s /q ".venv"
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  "%PYTHON_EXE%" -m venv .venv
  if errorlevel 1 (
    echo ERRO: Falha ao criar o ambiente virtual.
    pause
    exit /b 1
  )
) else (
  echo Ambiente virtual ja existe.
)

echo.
echo Atualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :erro

echo.
echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :erro

echo.
echo Instalando navegador do Playwright...
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto :erro

echo.
echo ==========================================
echo Instalacao concluida com sucesso.
echo Agora execute iniciar.bat
 echo ==========================================
pause
exit /b 0

:erro
echo.
echo ERRO: A instalacao nao terminou corretamente.
pause
exit /b 1
