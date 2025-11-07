import numpy as np

class Spiral:
    def __init__(self, center=(320, 240), inner_radius=0, outer_radius=200, turns=2, num_points=500):
        self.center = center
        self.inner_radius = inner_radius  # 0 → start at center
        self.outer_radius = outer_radius
        self.turns = turns
        self.num_points = num_points
        self.path_points = []
        self._generate_path()

    def _generate_path(self):
        """Generate spiral path points from center outward."""
        self.path_points = []
        theta = np.linspace(0, 2 * np.pi * self.turns, self.num_points)
        r_min = self.inner_radius
        r_max = self.outer_radius

        for t in theta:
            # Linear increase of radius from center
            r = r_min + (r_max - r_min) * t / (2 * np.pi * self.turns)
            x = self.center[0] + r * np.cos(t)
            y = self.center[1] + r * np.sin(t)
            self.path_points.append((int(x), int(y)))

    def get_reference_dot(self, progress):
        """
        Get the position of the reference dot along the spiral path.
        progress: float between 0 and 1
        """
        index = int(progress * (len(self.path_points) - 1))
        return self.path_points[index]

    def check_entry(self, finger_pos, entry_radius=30):
        """Check if finger is inside the start circle (center)."""
        if finger_pos is None:
            return False
        dx = finger_pos[0] - self.center[0]
        dy = finger_pos[1] - self.center[1]
        distance = (dx**2 + dy**2)**0.5
        return distance <= entry_radius

    def check_depth(self, finger_z, target_z=0.5, tolerance=0.05):
        """Return depth color: red = too close, green = correct, blue = too far"""
        if finger_z is None:
            return 'gray'
        diff = finger_z - target_z
        if abs(diff) < tolerance:
            return 'green'
        elif diff < -tolerance:
            return 'red'
        else:
            return 'blue'
