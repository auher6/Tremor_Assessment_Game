import cv2
import numpy as np
class Renderer:
    def draw_spiral(self, frame, spiral, finger_depth_color='yellow'):
        points = spiral.path_points
        cv2.polylines(frame, [np.array(points, dtype=np.int32)], False, self.color_map(finger_depth_color), thickness=5)

    def color_map(self, color_name):
        # Map logical colors to BGR values
        colors = {
            'yellow': (0, 255, 255),
            'red': (0, 0, 255),
            'blue': (255, 0, 0),
            'green': (0, 255, 0),
            'gray': (128, 128, 128)
        }
        return colors.get(color_name, (0, 255, 255))

    def draw_trace(self, frame, trace_points):
        if len(trace_points) > 1:
            pts = [(p[0], p[1]) for p in trace_points]
            cv2.polylines(frame, [np.array(pts, np.int32)], False, (0,0,255), thickness=3)


    def draw_reference_dot(self, frame, position):
        cv2.circle(frame, position, 8, (0, 255, 0), -1)

    def draw_entry_exit_circles(self, frame, spiral, show_end=False, show_start=True):
        if show_start:
            cv2.circle(frame, spiral.center, spiral.inner_radius, (0, 255, 255), 2)
        if show_end:
            cv2.circle(frame, spiral.path_points[-1], 30, (0, 255, 255), 2)

    def draw_depth_feedback(self, frame, spiral_color):
        """
        Display feedback text depending on the user's depth relative to target.

        Args:
            frame: Current frame to draw on
            spiral_color: 'green', 'red', 'blue', 'gray'
        """
        if spiral_color == 'green':
            text = "Good depth"
            color = (0, 255, 0)  # green
        elif spiral_color == 'red':
            text = "Move further"
            color = (0, 0, 255)  # red
        elif spiral_color == 'blue':
            text = "Move closer"
            color = (255, 0, 0)  # blue
        else:  # gray or unknown
            text = "No finger detected"
            color = (200, 200, 200)  # gray

        cv2.putText(frame, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

