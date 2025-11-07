import cv2
import numpy as np
import time
from camera_manager import CameraManager
from finger_tracker import FingerTracker
from spiral import Spiral
from trace_manager import TraceManager
from renderer import Renderer
from game_state import GameState
from config_loader import load_config

def main():
    # Load config
    config = load_config("config.yaml")

    # Show instructions first
    show_instructions(config)

    # Initialize components
    camera = CameraManager()
    tracker = FingerTracker()
    spiral = Spiral(center=(320, 240), inner_radius=50, outer_radius=200, turns=2)
    trace_manager = TraceManager()
    renderer = Renderer()
    game_state = GameState()

    total_time = 0
    fps = 30
    speed_multiplier = 16.0
    start_circle_used = False
    end_circle_radius = 30

    window_name = config["display"].get("window_name", "Tremor Assessment Game")

    # Create a resizable full-screen window for camera feed
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1920, 1080)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        frame = camera.get_frame()
        if frame is None:
            break

        finger_pos = tracker.update(frame)

        # Check if user enters start circle
        if not start_circle_used and finger_pos is not None:
            if spiral.check_entry(finger_pos) and spiral.check_depth(finger_pos[2]) == 'green':
                start_circle_used = True
                game_state.state = GameState.TRACING
                trace_manager.start_trace()

        # Move reference dot along spiral
        if start_circle_used and game_state.state != GameState.FINISHED:
            progress = min(total_time * speed_multiplier / (fps * len(spiral.path_points)), 1.0)
            reference_dot_pos = spiral.get_reference_dot(progress)
        else:
            progress = 0
            reference_dot_pos = spiral.path_points[0]

        # Check if finger is in end circle
        finger_in_end = False
        if finger_pos is not None:
            dx = finger_pos[0] - spiral.path_points[-1][0]
            dy = finger_pos[1] - spiral.path_points[-1][1]
            distance = (dx**2 + dy**2)**0.5
            if distance <= end_circle_radius:
                finger_in_end = True

        # Stop tracing when reference dot reached end AND finger in end circle
        if start_circle_used and progress >= 1.0 and finger_in_end:
            game_state.state = GameState.FINISHED

        # Update trace
        if game_state.state == GameState.TRACING and finger_pos is not None:
            trace_manager.update_trace(finger_pos)

        # Determine spiral color
        if finger_pos is not None:
            spiral_color = spiral.check_depth(finger_pos[2])
        else:
            spiral_color = 'gray'

        # Show/hide circles
        show_start = not start_circle_used
        show_end = progress >= 1.0 and game_state.state != GameState.FINISHED

        # Render everything
        renderer.draw_spiral(frame, spiral, finger_depth_color=spiral_color)
        renderer.draw_trace(frame, trace_manager.get_trace())
        renderer.draw_reference_dot(frame, reference_dot_pos)
        renderer.draw_entry_exit_circles(frame, spiral, show_end=show_end, show_start=show_start)
        renderer.draw_depth_feedback(frame, spiral_color)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1)
        if key & 0xFF == 27:  # ESC
            break

        if start_circle_used and game_state.state != GameState.FINISHED:
            total_time += 1

    camera.release()
    cv2.destroyAllWindows()


def show_instructions(config):
    """
    Full-screen instruction screen.
    """
    width, height = 1920, 1080
    window_name = config["display"].get("window_name", "Tremor Assessment Game")
    screen = np.zeros((height, width, 3), dtype=np.uint8)

    instructions = config.get("instructions", [
        "Welcome to the Tremor Assessment Game!",
        "",
        "1. Position your hand in front of the camera.",
        "2. Enter the yellow circle to start tracing the spiral.",
        "3. Trace the spiral with your index finger.",
        "4. Keep your finger at the correct depth (green).",
        "5. Complete the spiral to finish the test.",
        "",
        "Press any key to begin..."
    ])

    y0, dy = 100, 80
    for i, line in enumerate(instructions):
        y = y0 + i * dy
        cv2.putText(screen, line, (100, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 3)

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, width, height)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    cv2.imshow(window_name, screen)
    cv2.waitKey(0)
    cv2.destroyWindow(window_name)


if __name__ == '__main__':
    main()
