@echo off
title Salumber Election Live Server 2026
color 0b
cls
echo =====================================================================
echo       SALUMBER DISTRICT PANCHAYATI RAJ ELECTIONS 2026
echo       High-Performance Real-Time Portal ^& SQLite Database Server
echo =====================================================================
echo.
echo  Starting Election Backend Server on http://localhost:8000 ...
echo.
echo  [1] TV Broadcast Screen : http://localhost:8000/
echo  [2] Operator Vote Entry : http://localhost:8000/entry
echo  [3] 1-Click Excel CSV   : http://localhost:8000/api/export_csv
echo.
echo =====================================================================
echo.

start http://localhost:8000/
start http://localhost:8000/entry

python app.py

pause
