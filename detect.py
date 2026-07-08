import cv2
import winsound
from ultralytics import YOLO

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

            # Demo ke liye scissors detect karo
            if label == "scissors":
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
    else:
        alarm_playing = False

    cv2.imshow("SafeRail AI", frame)

    key = cv2.waitKey(1) & 0xFF

    # Manual alarm (W key)
    if key == ord('w'):
        winsound.PlaySound(
            "mixkit-sound-alert-in-hall-1006.wav",
            winsound.SND_FILENAME | winsound.SND_ASYNC
        )

    # Quit
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()