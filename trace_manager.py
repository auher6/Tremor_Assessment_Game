class TraceManager:
    def __init__(self):
        self.trace_points = []

    def start_trace(self):
        self.trace_points = []

    def update_trace(self, finger_pos):
        if finger_pos:
            self.trace_points.append(finger_pos)

    def get_trace(self):
        return self.trace_points
    
    def clear_trace(self):
        self.trace_points = []
