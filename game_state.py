import math

class GameState:
    WAITING = 0
    TRACING = 1
    FINISHED = 2
    IDLE = 3

    def __init__(self):
        self.state = self.WAITING

    def update(self, finger_pos, spiral, reference_dot_pos, end_circle_pos):
        if self.state == self.WAITING:
            if spiral.check_entry(finger_pos):
                self.state = self.TRACING

        elif self.state == self.TRACING:
            if finger_pos is not None:
                fx, fy, _ = finger_pos
                ex, ey = end_circle_pos
                distance = math.sqrt((fx - ex)**2 + (fy - ey)**2)
                if distance < 30:  # threshold for end
                    self.state = self.FINISHED

        return self.state
