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

    camera = CameraManager()
    tracker = FingerTracker()
    spiral_cfg = config.get("spiral", {})
    spiral = Spiral(
        center=tuple(spiral_cfg.get("center", (320,240))),
        inner_radius=spiral_cfg.get("inner_radius", 50),
        outer_radius=spiral_cfg.get("outer_radius", 200),
        turns=spiral_cfg.get("turns", 2),
        num_points=spiral_cfg.get("num_points", 500)
    )

    trace_manager = TraceManager()
    renderer = Renderer()
    game_state = GameState()

    total_time = 0
    stage3_start_time = None
    fps = 30
    speed_multiplier = 16.0
    start_circle_used = False
    end_circle_radius = 30

    # Step instructions and durations (seconds)
    steps = [
        ("Move your finger and see its trace", 5),
        ("Observe the depth feedback", 5),
        ("Watch the reference dot move along the spiral", 5),
        ("Start from the yellow circle and trace", 0)  # 0 = indefinite
    ]
    current_step = 0
    step_start_time = time.time()

    window_name = config.get("display", {}).get("window_name", "Tremor Assessment Game")
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("⚠️ No camera frame detected. Exiting.")
                break

            finger_pos = tracker.update(frame)

            # -----------------------
            # Step progression based on elapsed time
            # -----------------------
            elapsed = time.time() - step_start_time
            step_text, step_duration = steps[current_step]
            if step_duration > 0 and elapsed >= step_duration and current_step < len(steps) - 1:
                current_step += 1
                step_start_time = time.time()
                # Clear trace after Stage 1
                if current_step == 1 and hasattr(trace_manager, "clear_trace"):
                    trace_manager.clear_trace()

            # -----------------------
            # Instructions text (blue) at top-left
            # -----------------------
            cv2.putText(frame, f"{step_text}", 
                        (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2)

            # -----------------------
            # Finger trace
            # -----------------------
            if current_step == 0 and finger_pos is not None:
                trace_manager.update_trace(finger_pos)
                renderer.draw_trace(frame, trace_manager.get_trace())

            # -----------------------
            # Depth feedback (bottom-left)
            # -----------------------
            if current_step >= 1:
                depth_status = "N/A"
                if finger_pos is not None:
                    spiral_color = spiral.check_depth(finger_pos[2])
                    if spiral_color == "green":
                        depth_status = "Good depth"
                    elif spiral_color == "red":
                        depth_status = "Move further"
                    elif spiral_color == "blue":  # or whatever your check_depth returns
                        depth_status = "Move closer"
                    else:
                        depth_status = "Adjust depth"

                cv2.putText(frame, depth_status,
                            (10, frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0,255,0) if spiral_color=='green' else (0,0,255) if spiral_color=='red' else (200,200,200), 2)

            # -----------------------
            # Reference dot moving along spiral
            # -----------------------
            if current_step == 2:
                if stage3_start_time is None:
                    stage3_start_time = time.time()  # initialize when entering stage 3
                elapsed_stage3 = time.time() - stage3_start_time
                progress = min(elapsed_stage3 * speed_multiplier / len(spiral.path_points), 1.0)
                reference_dot_pos = spiral.get_reference_dot(progress)
                renderer.draw_reference_dot(frame, reference_dot_pos)

            # -----------------------
            # Stage 4: actual game
            # -----------------------
            if current_step == 3:
                # Check start circle entry
                if not start_circle_used and finger_pos is not None:
                    if spiral.check_entry(finger_pos) and spiral.check_depth(finger_pos[2]) == 'green':
                        start_circle_used = True
                        game_state.state = GameState.TRACING
                        trace_manager.start_trace()

                # Update reference dot for game
                if start_circle_used and game_state.state != GameState.FINISHED:
                    progress = min(total_time * speed_multiplier / (fps * len(spiral.path_points)), 1.0)
                    reference_dot_pos = spiral.get_reference_dot(progress)
                    renderer.draw_reference_dot(frame, reference_dot_pos)
                else:
                    progress = 0
                    reference_dot_pos = spiral.path_points[0]

                # End circle check
                finger_in_end = False
                if finger_pos is not None:
                    dx = finger_pos[0] - spiral.path_points[-1][0]
                    dy = finger_pos[1] - spiral.path_points[-1][1]
                    if (dx**2 + dy**2)**0.5 <= end_circle_radius:
                        finger_in_end = True

                # Finish tracing
                if start_circle_used and progress >= 1.0 and finger_in_end:
                    game_state.state = GameState.FINISHED

                # Update trace if tracing
                if start_circle_used and game_state.state == GameState.TRACING and finger_pos is not None:
                    trace_manager.update_trace(finger_pos)

                # Draw game trace (kept after finishing)
                renderer.draw_trace(frame, trace_manager.get_trace())

            # -----------------------
            # Render spiral
            # -----------------------
            renderer.draw_spiral(frame, spiral, finger_depth_color=spiral_color if current_step>=1 else None)

            # -----------------------
            # Show start/end circles for Stage 4
            # -----------------------
            show_start = not start_circle_used
            show_end = current_step==3 and progress >= 1.0 and game_state.state != GameState.FINISHED
            renderer.draw_entry_exit_circles(frame, spiral, show_end=show_end, show_start=show_start)

            # -----------------------
            # Show frame
            # -----------------------
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(10) & 0xFF
            if key == 27:
                print("⏹️ User pressed ESC. Exiting.")
                break

            if start_circle_used and game_state.state != GameState.FINISHED:
                total_time += 1

    except KeyboardInterrupt:
        print("⏹️ Keyboard interrupt received. Exiting.")

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
