@echo off
echo ====================================
echo CONFIGURATION BROKER LOCAL
echo ====================================
echo.
echo Cette configuration utilise Docker Mosquitto LOCAL au lieu du Raspberry Pi
echo.
echo ETAPES:
echo 1. Modifier .env du backend
echo 2. Flasher ESP8266 avec IP locale
echo 3. Redemarrer tout
echo.
echo ====================================
pause

cd digital-twin-backend

echo Sauvegarde .env...
copy .env .env.raspberry.backup

echo Configuration pour localhost...
powershell -Command "(Get-Content .env) -replace 'MQTT_BROKER=172.20.10.3', 'MQTT_BROKER=localhost' | Set-Content .env"

echo.
echo ====================================
echo .env configure pour localhost
echo ====================================
echo.
echo IMPORTANT: Flasher ESP8266 avec:
echo   #define MQTT_BROKER "172.20.10.2"
echo.
echo Pour revenir au Raspberry:
echo   copy .env.raspberry.backup .env
echo.
pause
