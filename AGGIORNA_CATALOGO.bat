@echo off
chcp 65001 > nul
title Fatto a Mano — Aggiornamento Automatico Catalogo & Vercel
color 0E

echo ==============================================================================
echo                FATTO A MANO — ATELIER DEL RAME PURO 99.9%%
echo           Sincronizzazione Automatica Immagini, Catalogo ^& Vercel
echo ==============================================================================
echo.
echo [1/3] Rilevamento cartelle e immagini in assets/...
echo [2/3] Sincronizzazione Supabase Storage e Database...
echo [3/3] Aggiornamento Vercel Live via GitHub...
echo.

cd /d "%~dp0"

python sync_catalog.py

echo.
echo ==============================================================================
echo Operazione conclusa!
echo Verifica il sito live su: https://fattoamano-alpha.vercel.app
echo ==============================================================================
echo.
pause
