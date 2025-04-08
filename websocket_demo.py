import argparse
import time
import json
import os
from websocket import create_connection
import cv2
import numpy as np

from main_controller import MainController
from utils import Drawer, Event, targets

class WebSocketClient:
    def __init__(self, url="ws://localhost:8000/ws"):
        self.url = url
        self.ws = None
        self.retry_count = 0
        self.max_retries = 5
        
    def connect(self):
        try:
            self.ws = create_connection(self.url, timeout=5)
            self.retry_count = 0
        except Exception as e:
            print(f"Connection failed: {e}")
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                time.sleep(1)
                self.connect()
                
    def receive_event(self):
        if self.ws:
            try:
                message = self.ws.recv()
                print(f"Received: {message}")
            except Exception as e:
                print(f"Receive error: {e}")
                self.connect()

    def send_event(self, event_data):
        print('Trying to send...')
        if not self.ws:
            self.connect()
        try:
            print("Sending event:", event_data)
            self.ws.send(json.dumps(event_data))
        except Exception as e:
            print(f"Send error: {e}")
            self.connect()
            self.send_event(event_data)  

def run(args):
    ws_client = WebSocketClient()
    
    # Определяем источник видео: если указан аргумент --video, используем его,
    # иначе берём значение из переменной окружения RTSP_URL или дефолтное видео
    video_path = args.video if args.video else os.getenv("RTSP_URL", "./videos/video1.mp4")
    print(f"Using video source: {video_path}")
    
    # Replace your VideoCapture initialization with:
    cap = cv2.VideoCapture()
    while not cap.isOpened():
        cap.open(video_path, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print("Retrying video connection...")
            time.sleep(1)
            
    # Настройка разрешения (при необходимости)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    controller = MainController(args.detector, args.classifier)
    drawer = Drawer()
    debug_mode = args.debug
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Video stream ended or frame not received.")
                break

            # Отзеркаливаем кадр
            frame = cv2.flip(frame, 1)

            start_time = time.time()
            bboxes, ids, labels = controller(frame)
            if debug_mode:
                if bboxes is not None:
                    bboxes = bboxes.astype(np.int32)
                    for i in range(bboxes.shape[0]):
                        box = bboxes[i, :]
                        gesture = targets[labels[i]] if labels[i] is not None else "None"
                        print(f"Frame detected: ID {ids[i]} : {gesture}, Box: {box}")
                fps = 1.0 / (time.time() - start_time)
                print(f"fps: {fps:.2f}")

            if len(controller.tracks) > 0:
                for trk in controller.tracks:
                    if trk["tracker"].time_since_update < 1 and trk['hands']:
                        gesture = trk['hands'][-1].gesture
                        if gesture in [
                            Event.SWIPE_LEFT, Event.SWIPE_LEFT2, Event.SWIPE_LEFT3,
                            Event.SWIPE_RIGHT, Event.SWIPE_RIGHT2, Event.SWIPE_RIGHT3,
                            Event.SWIPE_UP, Event.SWIPE_DOWN,
                            Event.ZOOM_IN, Event.ZOOM_OUT,
                            Event.TAP, Event.DOUBLE_TAP,
                        ]:
                            event_data = {
                                "event": gesture,
                                "track_id": int(ids[0]) if ids else -1,
                                "timestamp": time.time(),
                            }
                            ws_client.send_event(event_data)
                            trk["hands"].action = None

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        print("Exiting processing loop.")
        cap.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run gesture recognition demo")
    parser.add_argument("--detector", required=True, type=str, help="Path to detector ONNX model")
    parser.add_argument("--classifier", required=True, type=str, help="Path to classifier ONNX model")
    parser.add_argument("--debug", required=False, action="store_true", help="Enable debug mode")
    parser.add_argument("--video", required=False, type=str, help="Path to video file or RTSP URL")
    args = parser.parse_args()
    run(args)
