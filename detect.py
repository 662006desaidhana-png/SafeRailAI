import cv2
import os
import winsound
from ultralytics import YOLO
from datetime import datetime

# Load YOLO Model
model = YOLO("yolov8n.pt")

# Open Camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera not found!")
    exit()

print("Camera Started Successfully")

alarm_playing = False

while True:
    ret, frame = cap.read()
        
    if not ret:
        break

    cv2.putText(
        frame,
        "AI Monitoring Active",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    results = model(frame)

    suspicious = False

    for r in results:
        for box in r.boxes:

            cls = int(box.cls[0])
            label = model.names[cls]

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            print("Detected:", label)

            # Demo ke liye scissors ko suspicious maan rahe hain
            if label == "scissors":
                suspicious = True

    if suspicious:

        cv2.putText(
            frame,
            "WARNING! Suspicious Object Detected",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

        if not alarm_playing:

            alarm_playing = True

            if os.path.exists("mixkit-sound-alert-in-hall-1006.wav"):
                winsound.PlaySound(
                    "mixkit-sound-alert-in-hall-1006.wav",
                    winsound.SND_FILENAME | winsound.SND_ASYNC
                )

            os.makedirs("incidents", exist_ok=True)

            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.jpg")

            cv2.imwrite(os.path.join("incidents", filename), frame)

            print("Incident Saved")

    else:
        alarm_playing = False

    cv2.imshow("SafeRailAI", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
