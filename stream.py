import cv2
import os
import sqlite3
import platform
from datetime import datetime
from ultralytics import YOLO

# Windows par local alarm support
if platform.system() == "Windows":
    import winsound
else:
    winsound = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(BASE_DIR, "database.db")

INCIDENT_FOLDER = os.path.join(
    BASE_DIR,
    "incidents"
)

os.makedirs(INCIDENT_FOLDER, exist_ok=True)

# Make sure incidents table exists
def init_incidents_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            object_name TEXT NOT NULL,
            image TEXT
        )
    """)

    conn.commit()
    conn.close()


init_incidents_table()

# Load YOLO model
model = YOLO(
    os.path.join(BASE_DIR, "yolov8n.pt")
)

# Camera
camera = cv2.VideoCapture(0)

alarm_playing = False


def play_alarm():
    global alarm_playing

    if platform.system() == "Windows" and winsound:
        sound_file = os.path.join(
            BASE_DIR,
            "mixkit-sound-alert-in-hall-1006.wav"
        )

        if os.path.exists(sound_file):
            winsound.PlaySound(
                sound_file,
                winsound.SND_FILENAME | winsound.SND_ASYNC
            )

    alarm_playing = True


def stop_alarm():
    global alarm_playing

    if platform.system() == "Windows" and winsound:
        winsound.PlaySound(
            None,
            winsound.SND_ASYNC
        )

    alarm_playing = False


def generate_frames():
    global alarm_playing

    while True:

        success, frame = camera.read()

        if not success:
            break

        results = model(frame)

        annotated_frame = results[0].plot()

        suspicious = False
        detected_object = None

        for result in results:

            for box in result.boxes:

                cls = int(box.cls[0])

                label = model.names[cls].lower()

                if label in ["knife", "scissors", "gun"]:

                    suspicious = True
                    detected_object = label

        # Monitoring status
        cv2.putText(
            annotated_frame,
            "AI Monitoring Active",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        if suspicious:

            # Warning banner
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

            # Save incident image
            now = datetime.now()

            filename = now.strftime(
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

            # Save incident in database
            date = now.strftime("%d-%m-%Y")
            time = now.strftime("%H:%M:%S")

            conn = sqlite3.connect(DATABASE)

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

            print(
                "Incident saved:",
                filename
            )

            # Local alarm only works on Windows
            if not alarm_playing:
                play_alarm()

        else:

            stop_alarm()

        # Encode frame
        ret, buffer = cv2.imencode(
            ".jpg",
            annotated_frame
        )

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )