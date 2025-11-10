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
    spiral_main = Spiral(
        center=tuple(spiral_cfg.get("center", (320, 240))),
        inner_radius=spiral_cfg.get("inner_radius", 50),
        outer_radius=spiral_cfg.get("outer_radius", 200),
        turns=spiral_cfg.get("turns", 2),
        num_points=spiral_cfg.get("num_points", 500)
    )

    # Create second (smaller) spiral — tighter and smaller radius
    spiral_small = Spiral(
        center=tuple(spiral_cfg.get("center", (320, 240))),  # offset to the right
        inner_radius=int(spiral_cfg.get("inner_radius", 50) * 0.6),
        outer_radius=int(spiral_cfg.get("outer_radius", 200) * 0.6),
        turns=spiral_cfg.get("turns", 2),
        num_points=spiral_cfg.get("num_points", 500)
    )

    trace_manager = TraceManager()
    renderer = Renderer()
    game_state = GameState()

    game_cfg = config.get("game", {})
    display_cfg = config.get("display", {})

    total_time = 0
    stage3_start_time = None
    stage5_start_time = None
    fps = display_cfg.get("fps", 30)

    speed_multiplier = game_cfg.get("speed_multiplier", 16.0)
    #speed_multiplier = 16.0
    start_circle_used = False
    small_start_circle_used = False
    end_circle_radius = 30
    
    # Countdown variables
    countdown_start_time = None
    countdown_active = False
    countdown_duration = 3  # 3 seconds

    # Step instructions and durations (seconds)
    steps = [
        ("Move your finger and see its trace", 5),
        ("Observe the depth feedback", 5),
        ("Watch the reference dot move", 5),
        ("Get ready to trace the spiral", 0),  # Countdown before main spiral
        ("Start at the blue circle and trace", 0),       # main spiral tracing
        ("Get ready to trace the spiral", 0),  # Countdown before small spiral
        ("Follow the blue dot", 0)        # second spiral phase (reverse)
    ]
    current_step = 0
    step_start_time = time.time()

    window_name = display_cfg.get("window_name", "Tremor Assessment")
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
            
            # Handle countdown steps
            if current_step in [3, 5] and not countdown_active:  # Countdown steps
                countdown_active = True
                countdown_start_time = time.time()
            
            if countdown_active:
                countdown_elapsed = time.time() - countdown_start_time
                countdown_remaining = max(0, countdown_duration - int(countdown_elapsed))
                
                if countdown_remaining > 0:
                    # Show countdown in the top-right corner to avoid interference
                    countdown_text = str(countdown_remaining)
                    text_size = cv2.getTextSize(countdown_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 4)[0]
                    text_x = frame.shape[1] - text_size[0] - 20  # Right side
                    text_y = 60  # Top area
                    cv2.putText(frame, countdown_text, (text_x, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
                else:
                    # Countdown finished, move to next step
                    countdown_active = False
                    current_step += 1
                    step_start_time = time.time()
                    if current_step == 4:  # After main spiral countdown
                        trace_manager.clear_trace()
                    elif current_step == 6:  # After small spiral countdown  
                        trace_manager.clear_trace()
            elif step_duration > 0 and elapsed >= step_duration and current_step < len(steps) - 1:
                current_step += 1
                step_start_time = time.time()
                if current_step == 1 and hasattr(trace_manager, "clear_trace"):
                    trace_manager.clear_trace()

            # -----------------------
            # Instructions text (blue, top-center)
            # -----------------------
            if not countdown_active or current_step not in [3, 5]:
                text_x = frame.shape[1] // 2 - len(step_text) * 6
                cv2.putText(frame, step_text, (text_x, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            # -----------------------
            # Finger trace for Stage 1
            # -----------------------
            if current_step == 0 and finger_pos is not None and not countdown_active:
                trace_manager.update_trace(finger_pos)

            # -----------------------
            # Depth feedback (bottom-left)
            # -----------------------
            spiral_color = None
            if current_step >= 1 and not countdown_active:
                depth_status = "N/A"
                if finger_pos is not None:
                    # Use appropriate spiral for depth check
                    if current_step < 5:  # Updated for new step indices
                        spiral_color = spiral_main.check_depth(finger_pos[2])
                    else:
                        spiral_color = spiral_small.check_depth(finger_pos[2])
                        
                    if spiral_color == "green":
                        depth_status = "Good depth"
                    elif spiral_color == "red":
                        depth_status = "Move further"
                    elif spiral_color == "blue":
                        depth_status = "Move closer"
                    else:
                        depth_status = "Adjust depth"

                cv2.putText(frame, depth_status,
                            (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 255, 0) if depth_status == "Good depth" else (0, 0, 255)
                            if "further" in depth_status else (200, 200, 200), 2)

            # -----------------------
            # Stage 3: reference dot moving on main spiral
            # -----------------------
            if current_step == 2 and not countdown_active:
                if stage3_start_time is None:
                    stage3_start_time = time.time()
                elapsed_stage3 = time.time() - stage3_start_time
                progress = min(elapsed_stage3 * speed_multiplier / len(spiral_main.path_points), 1.0)
                reference_dot_pos = spiral_main.get_reference_dot(progress)
                # Reference dot will be drawn after spiral

            # -----------------------
            # Stage 4: main spiral tracing (normal direction)
            # -----------------------
            main_spiral_completed = False
            if current_step == 4 and not countdown_active:  # Updated step index
                if not start_circle_used and finger_pos is not None:
                    if spiral_main.check_entry(finger_pos) and spiral_main.check_depth(finger_pos[2]) == 'green':
                        start_circle_used = True
                        game_state.state = GameState.TRACING
                        trace_manager.start_trace()

                if start_circle_used and game_state.state != GameState.FINISHED:
                    progress = min(total_time * speed_multiplier / (fps * len(spiral_main.path_points)), 1.0)
                    reference_dot_pos = spiral_main.get_reference_dot(progress)
                else:
                    progress = 0
                    reference_dot_pos = spiral_main.path_points[0]

                # End circle check (at the outer end for main spiral)
                finger_in_end = False
                if finger_pos is not None:
                    dx = finger_pos[0] - spiral_main.path_points[-1][0]
                    dy = finger_pos[1] - spiral_main.path_points[-1][1]
                    if (dx ** 2 + dy ** 2) ** 0.5 <= end_circle_radius:
                        finger_in_end = True

                if start_circle_used and progress >= 1.0 and finger_in_end:
                    game_state.state = GameState.FINISHED
                    main_spiral_completed = True
                    current_step = 5  # proceed to countdown for small spiral
                    step_start_time = time.time()
                    trace_manager.clear_trace()
                    total_time = 0
                    stage3_start_time = None
                    start_circle_used = False
                    # Reset small spiral tracking variables
                    small_start_circle_used = False

                if start_circle_used and game_state.state == GameState.TRACING and finger_pos is not None:
                    trace_manager.update_trace(finger_pos)

            # -----------------------
            # Stage 6: Smaller spiral (REVERSE direction)
            # -----------------------
            small_spiral_completed = False
            if current_step == 6 and not countdown_active:  # Updated step index
                if stage5_start_time is None:
                    stage5_start_time = time.time()

                # REVERSE START: Check if finger is at the OUTER END (last point) with good depth
                if not small_start_circle_used and finger_pos is not None:
                    # Manual check for outer end (reverse start position)
                    dx_start = finger_pos[0] - spiral_small.path_points[-1][0]  # Outer end
                    dy_start = finger_pos[1] - spiral_small.path_points[-1][1]
                    distance_to_start = (dx_start ** 2 + dy_start ** 2) ** 0.5
                    
                    if distance_to_start <= end_circle_radius and spiral_small.check_depth(finger_pos[2]) == 'green':
                        small_start_circle_used = True
                        game_state.state = GameState.TRACING
                        trace_manager.start_trace()
                        stage5_start_time = time.time()  # Reset timer when starting

                # REVERSE PROGRESS: Progress goes from 1.0 to 0.0
                if small_start_circle_used and game_state.state != GameState.FINISHED:
                    elapsed_small = time.time() - stage5_start_time
                    progress_small = max(1.0 - min(elapsed_small * speed_multiplier / len(spiral_small.path_points), 1.0), 0.0)
                    # Get reverse reference dot position
                    reference_dot_pos = spiral_small.get_reference_dot(progress_small)
                else:
                    progress_small = 1.0  # Start from the end for reverse spiral
                    reference_dot_pos = spiral_small.path_points[-1]  # Show at outer end initially

                # REVERSE END CHECK: End circle is now at the inner center (first point)
                finger_in_end_small = False
                if finger_pos is not None:
                    dx_end = finger_pos[0] - spiral_small.path_points[0][0]  # Check inner center
                    dy_end = finger_pos[1] - spiral_small.path_points[0][1]
                    distance_to_end = (dx_end ** 2 + dy_end ** 2) ** 0.5
                    if distance_to_end <= end_circle_radius:
                        finger_in_end_small = True

                # REVERSE COMPLETION: Complete when progress reaches 0 and finger is at inner center
                if small_start_circle_used and progress_small <= 0.0 and finger_in_end_small:
                    game_state.state = GameState.FINISHED
                    small_spiral_completed = True
                    print("✅ Both spirals completed!")
                    # Optional: You could add a completion message or next step here

                # Update trace for small spiral
                if small_start_circle_used and game_state.state == GameState.TRACING and finger_pos is not None:
                    trace_manager.update_trace(finger_pos)

            # -----------------------
            # RENDERING ORDER: Spirals -> Reference Dot -> Trace -> Circles
            # -----------------------
            
            # Draw spirals first (background)
            if current_step < 5:  # Main spiral stages
                renderer.draw_spiral(frame, spiral_main,
                                   finger_depth_color=spiral_color if current_step >= 1 else None)
            
            elif current_step >= 5:  # Small spiral stages  
                renderer.draw_spiral(frame, spiral_small,
                                   finger_depth_color=spiral_color if current_step >= 1 else None)

            # Draw reference dot second (on top of spiral)
            # SHOW DOTS DURING COUNTDOWN TOO - so user can position hand
            if ((current_step == 2 and not countdown_active) or 
                (current_step == 3) or  # Show dot during main spiral countdown
                (current_step == 4 and not countdown_active) or
                (current_step == 5) or  # Show dot during small spiral countdown
                (current_step == 6 and not countdown_active)):
                if current_step == 3:  # Main spiral countdown - show dot at start position
                    reference_dot_pos = spiral_main.path_points[0]
                elif current_step == 5:  # Small spiral countdown - show dot at start position (outer end)
                    reference_dot_pos = spiral_small.path_points[-1]
                elif 'reference_dot_pos' in locals():
                    # Use the calculated reference dot position
                    pass
                
                renderer.draw_reference_dot(frame, reference_dot_pos)

            # Draw trace third (on top of reference dot and spiral)
            if ((current_step == 0 and not countdown_active) or 
                (current_step == 4 and start_circle_used and not countdown_active) or
                (current_step == 6 and small_start_circle_used and not countdown_active)):
                renderer.draw_trace(frame, trace_manager.get_trace())

            # Draw circles last (on top of everything)
            # SHOW CIRCLES DURING COUNTDOWN TOO - so user can see where to start
            if (current_step == 3) or (current_step == 4 and not countdown_active):  # Main spiral stages
                # Draw main spiral for stages 3-4 (including countdown)
                show_start = not start_circle_used and (current_step == 3 or current_step == 4)
                show_end = current_step == 4 and progress >= 1.0 and game_state.state != GameState.FINISHED
                renderer.draw_entry_exit_circles(frame, spiral_main,
                                               show_end=show_end, show_start=show_start)
            
            elif (current_step == 5) or (current_step == 6 and not countdown_active):  # Small spiral stages
                # Draw small spiral for stage 5-6 (including countdown)
                show_start_small = not small_start_circle_used and (current_step == 5 or current_step == 6)
                show_end_small = current_step == 6 and progress_small <= 0.0 and game_state.state != GameState.FINISHED
                
                # Manual circles for reverse spiral
                if show_start_small:
                    cv2.circle(frame, 
                              (int(spiral_small.path_points[-1][0]), int(spiral_small.path_points[-1][1])),
                              end_circle_radius, (0, 255, 255), 2)  # Yellow circle
                
                if show_end_small:
                    cv2.circle(frame,
                              (int(spiral_small.path_points[0][0]), int(spiral_small.path_points[0][1])),
                              end_circle_radius, (0, 255, 0), 2)  # Green circle

            # -----------------------
            # Show frame
            # -----------------------
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(10) & 0xFF
            if key == 27:
                print("⏹️ User pressed ESC. Exiting.")
                break

            if (start_circle_used and game_state.state != GameState.FINISHED and 
                current_step == 4 and not countdown_active):
                total_time += 1

    except KeyboardInterrupt:
        print("⏹️ Keyboard interrupt received. Exiting.")
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()