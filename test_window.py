import cv2
import numpy as np

# Create a dummy frame
frame = np.zeros((480, 640, 3), dtype=np.uint8)

# Show the frame in a window
cv2.imshow("Test", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
