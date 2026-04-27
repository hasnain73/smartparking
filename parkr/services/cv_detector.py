import numpy as np
import cv2

def detect_parking_status(image_bytes: bytes) -> dict:
    """
    Analyzes an image to detect if a parking spot is free or occupied.
    Currently uses a simplified mock logic that returns a stable result
    based on image brightness to simulate detection.
    """
    try:
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Could not decode image")

        # Simplified logic: use brightness as a proxy for 'free' (higher) vs 'occupied' (lower)
        # In a real app, this would be a YOLO/CNN model call.
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        
        # Determine status
        status = "free" if avg_brightness > 120 else "occupied"
        confidence = 0.85 if avg_brightness > 120 else 0.75

        return {
            "status": status,
            "confidence": confidence
        }
    except Exception as e:
        # Fallback for errors
        return {
            "status": "free",
            "confidence": 0.5,
            "error": str(e)
        }
