import numpy as np
import cv2


def detect_parking_status(image_bytes: bytes) -> dict:
    """
    Analyzes an image to detect if a parking spot is free or occupied.
    Uses brightness as a simple proxy for occupancy.
    Always returns a safe result — never raises.
    """
    try:
        if not image_bytes:
            return {"status": "unknown", "confidence": 0.5, "error": "Empty image data"}

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return {"status": "unknown", "confidence": 0.5, "error": "Could not decode image"}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        avg_brightness = float(np.mean(gray))

        if avg_brightness > 120:
            return {"status": "free", "confidence": round(min(avg_brightness / 255, 0.95), 2)}
        else:
            return {"status": "occupied", "confidence": round(1.0 - avg_brightness / 255, 2)}

    except Exception as e:
        # Safe fallback — never crash the API
        return {"status": "unknown", "confidence": 0.5, "error": str(e)}
