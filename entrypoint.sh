#!/bin/sh
# Запускаем FastAPI сервер в фоне
uvicorn server:app --host 0.0.0.0 --port 8000 &
# Ждем 2 секунды для старта сервера
sleep 2
# Запускаем демо обработки видеопотока
python websocket_demo.py --detector models/hand_detector.onnx --classifier models/crops_classifier.onnx --debug
