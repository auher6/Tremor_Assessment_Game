import cv2
import numpy as np
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Spiral function
def draw_spiral(frame, center, turns=3, radius_step=10, color=(0, 255, 0), thickness=2):
    h, w, _ = frame.shape
    spiral_points = []
    for i in range(360 * turns):
        angle = np.deg2rad(i)
        radius = radius_step * i / 360
        x = int(center[0] + radius * np.cos(angle))
        y = int(center[1] + radius * np.sin(angle))
        spiral_points.append((x, y))
    for i in range(1, len(spiral_points)):
        cv2.line(frame, spiral_points[i - 1], spiral_points[i], color, thickness)

# Webcam setup
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # mirror view
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # Draw spiral in center
    center = (frame.shape[1] // 2, frame.shape[0] // 2)
    draw_spiral(frame, center)

    # Draw hand landmarks
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Spiral Hand Tracker", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
        break

cap.release()
cv2.destroyAllWindows()
