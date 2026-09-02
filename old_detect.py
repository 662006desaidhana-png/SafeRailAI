import cv2
import os
import winsound
import sqlite3
from ultralytics import YOLO
from datetime import datetime

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

alarm_playing = False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # AI Active text
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
            print("Detected:",label)

            # Demo ke liye scissors detect karo
        if label == "scissors": 
            print("Detected:",label)                 
            suspicious = True

    # Automatic alert
    if suspicious:
        cv2.putText(
            frame,
            "WARNING! Possible Suspicious Object",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

        if not alarm_playing:
            winsound.PlaySound(
        "mixkit-sound-alert-in-hall-1006.wav",
                winsound.SND_FILENAME | winsound.SND_ASYNC
            )
            alarm_playing = True
        if not incident_saved:

            os.makedirs("incidents", exist_ok=True)

            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.jpg")

            filepath = os.path.join("static/incidents", filename)
        
            cv2.imwrite(filepath,annotated)

            print("Incident Saved:", filepath)

            now = datetime.now()

            date = now.strftime("%d-%m-%Y")
            time = now.strftime("%H:%M:%S")

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO incidents(date, time, object_name, image) VALUES (?, ?, ?, ?)",
                (date, time, label, filename)
            )

            conn.commit()
            conn.close()
            
            incident_saved = True
    else:
        alarm_plpaying = False
        incident_saved = False

        annotated = frame

    cv2.imshow("SafeRail AI",annotated)

    key = cv2.waitKey(1) & 0xFF

    # Quit
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()