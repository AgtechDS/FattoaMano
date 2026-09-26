@echo off
chcp 65001 > nul
cls
echo ===============================================================================
echo            FATTO A MANO — BOUTIQUE ORAFA DEL RAME PURO 99.9%
echo ===============================================================================
echo [1/2] Verifica ambiente Python e dipendenze...
echo [2/2] Avvio Server Web e Gateway Stripe su http://localhost:8092 ...
echo.
start "" http://localhost:8092
python "%~dp0server.py" 8092
pause
