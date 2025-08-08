@echo off
echo === Kafka Setup for Real-time Pricing ===
echo.

:menu
echo [1] Start Kafka Server (Docker)
echo [2] Stop Kafka Server
echo [3] Start Data Producer
echo [4] Check Kafka Topics
echo [5] Start FastAPI App
echo [6] View Kafka UI
echo [0] Exit
echo.
set /p choice=Choose option: 

if "%choice%"=="1" goto start_kafka
if "%choice%"=="2" goto stop_kafka
if "%choice%"=="3" goto start_producer
if "%choice%"=="4" goto check_topics
if "%choice%"=="5" goto start_app
if "%choice%"=="6" goto kafka_ui
if "%choice%"=="0" goto exit
goto menu

:start_kafka
echo Starting Kafka server with Docker...
docker-compose up -d
echo.
echo ✅ Kafka started! 
echo - Kafka: localhost:9092
echo - Kafka UI: http://localhost:8080
echo.
pause
goto menu

:stop_kafka
echo Stopping Kafka server...
docker-compose down
echo ✅ Kafka stopped!
echo.
pause
goto menu

:start_producer
echo Starting data producer...
python kafka_producer.py
pause
goto menu

:check_topics
echo Checking Kafka topics...
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
echo.
pause
goto menu

:start_app
echo Starting FastAPI application...
python run_fastapi.py
pause
goto menu

:kafka_ui
echo Opening Kafka UI...
start http://localhost:8080
goto menu

:exit
echo Goodbye!
pause
