@echo off
title Salumber Election Server + Cloudflare Public Live Tunnel
color 0b
cls
echo =====================================================================
echo       SALUMBER DISTRICT PANCHAYATI RAJ ELECTIONS 2026
echo       Local SQLite Database + Cloudflare Live Public Broadcast
echo =====================================================================
echo.
echo  [1] Starting Local Election Engine on http://localhost:8000 ...
start /B python app.py
timeout /t 2 >nul

echo.
echo  [2] Opening Local Operator Console and TV Display in browser...
start http://localhost:8000/
start http://localhost:8000/entry

echo.
echo =====================================================================
echo  [3] CONNECTING TO CLOUDFLARE GLOBAL NETWORK...
echo =====================================================================
echo.
echo  Look for the line starting with "https://....trycloudflare.com" below.
echo  Copy and share that HTTPS link for Live Online Broadcast anywhere in the world!
echo.
echo =====================================================================
echo.

cloudflared tunnel --url http://localhost:8000

pause
