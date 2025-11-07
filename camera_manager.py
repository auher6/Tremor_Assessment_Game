import cv2

class CameraManager:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return cv2.flip(frame, 1)  # mirror view

    def release(self):
        self.cap.release()
