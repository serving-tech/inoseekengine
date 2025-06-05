import time
import cv2
import easyocr
import requests
from django.conf import settings

def process_frame(frame, parking_space_id):
    reader = easyocr.Reader(['en'])
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray)
    for (bbox, text, prob) in results:
        if prob > 0.7:
            number_plate = text.upper().replace(' ', '')
            response = requests.post(
                f"{settings.API_BASE_URL}/api/check-number-plate/",
                json={'number_plate': number_plate, 'parking_space_id': parking_space_id}
            )
            return response.json()
    return {'status': 'no_plate', 'message': 'No number plate detected'}

def run_cctv(stream_url, parking_space_id):
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("Error: Could not open video stream")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame")
            break
        result = process_frame(frame, parking_space_id)
        print(result)
        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        time.sleep(5)

    cap.release()
    cv2.destroyAllWindows()