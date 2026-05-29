@echo off
echo ============================================
echo   AI-PECOo — Device ID Fetcher
echo ============================================
echo.

set SERVER=http://localhost:8000

echo Step 1: Logging in as admin@aipeco.com ...
echo.

curl -s -X POST %SERVER%/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"admin@aipeco.com\", \"password\": \"admin123\"}" ^
  > login_response.json

echo Login response saved. Extracting token...
echo.

REM Display the full device list with token
for /f "tokens=2 delims=:," %%a in ('findstr "access_token" login_response.json') do set TOKEN=%%~a
set TOKEN=%TOKEN:"=%
set TOKEN=%TOKEN: =%

echo Step 2: Fetching your devices...
echo.

curl -s -X GET %SERVER%/api/devices ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json"

echo.
echo.
echo ============================================
echo   Copy the "id" values from above and
echo   paste them into AIPECO.ino deviceIds[]
echo ============================================
echo.

del login_response.json 2>nul
pause
