import cv2
import winsound
import os
import sqlite3
from datetime import datetime
from ultralytics import YOLO

# ==========================
# YOLO MODEL
# ==========================
model = YOLO("yolov8n.pt")

# ==========================
# CAMERA
# ==========================
camera = cv2.VideoCapture(0)

# ==========================
# INCIDENT FOLDER
# ==========================
INCIDENT_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "incidents"
)

os.makedirs(INCIDENT_FOLDER, exist_ok=True)

# ==========================
# ALARM STATUS
# ==========================
alarm_playing = False


def generate_frames():

    global alarm_playing

    while True:

        success, frame = camera.read()

        if not success:
            break

        # ==========================
        # YOLO DETECTION
        # ==========================
        results = model(frame)

        annotated_frame = results[0].plot()

        suspicious = False
        detected_object = None

        # ==========================
        # CHECK DETECTIONS
        # ==========================
        for r in results:

            for box in r.boxes:

                cls = int(box.cls[0])

                label = model.names[cls].lower()

                # Keep this for your existing detection classes
                if label in ["knife", "scissors", "gun"]:
                    suspicious = True
                    detected_object = label

        # ==========================
        # AI MONITORING TEXT
        # ==========================
        cv2.putText(
            annotated_frame,
            "AI Monitoring Active",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # ==========================
        # WARNING
        # ==========================
        if suspicious:

            # RED BANNER
            cv2.rectangle(
                annotated_frame,
                (0, 0),
                (1280, 85),
                (0, 0, 255),
                -1
            )

            cv2.putText(
                annotated_frame,
                "WARNING: Suspicious Object Detected!",
                (20, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2
            )

            # ==========================
            # SAVE IMAGE
            # ==========================
            filename = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S-%f.jpg"
            )

            filepath = os.path.join(
                INCIDENT_FOLDER,
                filename
            )

            cv2.imwrite(
                filepath,
                annotated_frame
            )

            # ==========================
            # SAVE DATABASE
            # ==========================
            date = datetime.now().strftime("%d-%m-%Y")
            time = datetime.now().strftime("%H:%M:%S")

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO incidents
                (date, time, object_name, image)
                VALUES (?, ?, ?, ?)
                """,
                (
                    date,
                    time,
                    detected_object,
                    filename
                )
            )

            conn.commit()
            conn.close()

            print("Incident saved:", filename)

            # ==========================
            # ALARM
            # ==========================
            if not alarm_playing:

                alarm_playing = True

                sound_file = "mixkit-sound-alert-in-hall-1006.wav"

                if os.path.exists(sound_file):

                    winsound.PlaySound(
                        sound_file,
                        winsound.SND_FILENAME |
                        winsound.SND_ASYNC
                    )

        else:

            alarm_playing = False

            winsound.PlaySound(
                None,
                winsound.SND_ASYNC
            )

        # ==========================
        # CONVERT FRAME
        # ==========================
        ret, buffer = cv2.imencode(
            ".jpg",
            annotated_frame
        )

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        # ==========================
        # SEND VIDEO
        # ==========================
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )