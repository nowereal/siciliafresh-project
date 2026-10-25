@echo off
REM Esegue l'analisi e apre la pagina dei risultati (Windows).
cd /d "%~dp0"
python main.py
if errorlevel 1 (
  echo.
  echo Esecuzione non riuscita. Verificare che Python sia installato e i dati in data\ siano validi.
)
pause
