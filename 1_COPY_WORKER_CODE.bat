@echo off
title Copy worker.js to Clipboard
powershell -Command "Get-Content worker.js -Raw | Set-Clipboard"
echo.
echo =======================================================================
echo  SUCCESS: worker.js has been copied to your Windows Clipboard!
echo =======================================================================
echo.
echo  Now:
echo  1. Open Cloudflare Dashboard (Workers & Pages -^> countingdisplay)
echo  2. Click "Quick Edit" or "Edit code"
echo  3. Press Ctrl+A (Select All), then Ctrl+V (Paste)
echo  4. Click "Save and Deploy" at the top right!
echo.
echo =======================================================================
pause
