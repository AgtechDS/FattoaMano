@echo off
chcp 65001 > nul
cls
echo ===============================================================================
echo            AGOS ENTERPRISE: AVVIO TELEGRAM BOT FATTO A MANO
echo ===============================================================================
echo In ascolto su Telegram per nuove foto e creazioni da pubblicare...
echo.
python "%~dp0telegram-agos.py"
pause
