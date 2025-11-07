import mediapipe as mp
import cv2

class FingerTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1)
        self.mp_draw = mp.solutions.drawing_utils
        # approximate scale factor: 1 unit z = 1 meter (adjust experimentally)
        self.z_scale = 0.5  # adjust based on your camera distance

    def update(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            # use index fingertip
            fingertip = hand.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]

            h, w, _ = frame.shape
            x = int(fingertip.x * w)
            y = int(fingertip.y * h)
            # z normalized, multiply by scale to get meters
            z = fingertip.z * self.z_scale + 0.5  # offset so target_z = 0.5m at screen plane

            return (x, y, z)

        return None

