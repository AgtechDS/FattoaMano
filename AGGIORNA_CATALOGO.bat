@echo off
chcp 65001 > nul
title Fatto a Mano — Aggiornamento Automatico Catalogo & Vercel
color 0E

echo ==============================================================================
echo                FATTO A MANO — ATELIER DEL RAME PURO 99.9%%
echo           Sincronizzazione Automatica Immagini, Catalogo ^& Vercel
echo ==============================================================================
echo.

cd /d "%~dp0"
set PYTHONUNBUFFERED=1

:: 1. Ricerca interprete Python funzionante
set "PY_BIN="
if exist "D:\Users\Andre\anaconda3\python.exe" (
    set "PY_BIN=D:\Users\Andre\anaconda3\python.exe"
) else (
    for /f "tokens=*" %%i in ('where python 2^>nul') do (
        if not defined PY_BIN (
            set "PY_BIN=%%i"
        )
    )
)

if not defined PY_BIN (
    echo [ERRORE CRITICO] Nessun interprete Python valido trovato nel sistema!
    echo Assicurati che Python o Anaconda siano installati nel PATH.
    echo.
    pause
    exit /b 1
)

echo [INFO] Utilizzo interprete: %PY_BIN%
echo [1/3] Rilevamento cartelle e immagini in assets/...
echo [2/3] Sincronizzazione Supabase Storage e Database...
echo [3/3] Aggiornamento Vercel Live via GitHub...
echo.

"%PY_BIN%" -u sync_catalog.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ATTENZIONE] Lo script ha terminato con codice di stato: %ERRORLEVEL%
) else (
    echo.
    echo ==============================================================================
    echo ✅ SINCRONIZZAZIONE E DEPLOY COMPLETATI CON SUCCESSO!
    echo 👉 Dominio Ufficiale: https://agtechdesigne.shop
    echo 👉 Alias Vercel:     https://fattoamano-alpha.vercel.app
    echo ==============================================================================
)
echo.
pause
