import cv2
import time

from camera import get_camera
from detector import detect_objects
from ocr import detect_text
from formatter import format_output
from sender import send_to_backend

# ---------------- CONFIG ---------------- #

SEND_EVERY_N_FRAMES = 20      # send data every N frames
OCR_EVERY_N_FRAMES = 60       # OCR is slow, so run less frequently

# --------------------------------------- #

def main():
    cap = get_camera()

    frame_count = 0
    last_texts = []

    print("[INFO] Vision module started (headless mode)")
    print("[INFO] Press CTRL + C to stop")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Camera frame not received")
                break

            frame_count += 1

            # ---- YOLO OBJECT DETECTION ----
            objects = detect_objects(frame)

            # ---- OCR (RUN SPARINGLY) ----
            if frame_count % OCR_EVERY_N_FRAMES == 0:
                try:
                    last_texts = detect_text(frame)
                except Exception as e:
                    print("[WARN] OCR skipped:", repr(e))
                    last_texts = []

            # ---- SEND TO BACKEND (THROTTLED) ----
            if frame_count % SEND_EVERY_N_FRAMES == 0:
                payload = format_output(objects, last_texts)
                send_to_backend(payload)

    except KeyboardInterrupt:
        print("\n[INFO] Vision module stopped by user")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera released, cleanup done")


if __name__ == "__main__":
    main()
