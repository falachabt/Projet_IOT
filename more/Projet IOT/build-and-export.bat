@echo off
REM Script Windows pour build et export des images Docker

echo ========================================
echo Build et Export pour Raspberry Pi
echo ========================================
echo.

REM 1. Build des images
echo [1/4] Build des images Docker...
docker-compose build --no-cache
if errorlevel 1 (
    echo ERREUR: Build echoue
    pause
    exit /b 1
)

REM 2. Tag des images
echo.
echo [2/4] Tag des images...
docker tag iot_backend:latest iot_backend:latest
docker tag iot_frontend:latest iot_frontend:latest

REM 3. Export des images
echo.
echo [3/4] Export des images...
if not exist "docker-images" mkdir docker-images

echo   - Export mosquitto...
docker pull eclipse-mosquitto:2.0
docker save eclipse-mosquitto:2.0 -o docker-images\mosquitto.tar

echo   - Export backend...
docker save iot_backend:latest -o docker-images\backend.tar

echo   - Export frontend...
docker save iot_frontend:latest -o docker-images\frontend.tar

REM 4. Créer archive
echo.
echo [4/4] Creation archive...
tar -czf iot-jumeau-numerique-raspberry.tar.gz ^
    docker-compose.yml ^
    mosquitto ^
    start-raspberry.sh ^
    README_DIGITAL_TWIN.md ^
    DEMARRAGE_RAPIDE.md

REM Nettoyage
rmdir /s /q docker-images

echo.
echo ========================================
echo SUCCES!
echo ========================================
echo.
echo Fichier cree: iot-jumeau-numerique-raspberry.tar.gz
echo.
echo Prochaines etapes:
echo   1. Transferer sur Raspberry Pi:
echo      scp iot-jumeau-numerique-raspberry.tar.gz pi@^<IP^>:~/
echo.
echo   2. Sur le Raspberry Pi:
echo      tar -xzf iot-jumeau-numerique-raspberry.tar.gz
echo      chmod +x start-raspberry.sh
echo      ./start-raspberry.sh
echo.
pause
