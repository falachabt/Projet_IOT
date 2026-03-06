@echo off
echo ====================================
echo TEST CONNEXION MQTT RASPBERRY PI
echo ====================================
echo.
echo 1. Ping du Raspberry Pi (172.20.10.3)
ping -n 2 172.20.10.3
echo.
echo 2. Test backend API
curl -s http://localhost:3000/api/state
echo.
echo.
echo 3. Ecoute messages ESP8266 (5 secondes)
timeout /t 5 /nobreak >nul
echo.
echo ====================================
echo TEST TERMINE
echo ====================================
pause
