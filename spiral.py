import numpy as np

class Spiral:
    def __init__(self, center=(320, 240), inner_radius=0, outer_radius=200, turns=2, num_points=500):
        """
        Spiral path starting smoothly at the center and spiraling outward.

        Args:
            center: (x, y) tuple for spiral center
            inner_radius: ignored (kept for compatibility)
            outer_radius: maximum radius of the spiral
            turns: number of spiral turns
            num_points: total points along the spiral
        """
        self.center = center
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.turns = turns
        self.num_points = max(num_points, 2)
        self.path_points = []
        self._generate_path()

    def _generate_path(self):
        self.path_points = []

        # Create a very fine theta array
        theta_fine = np.linspace(0, 2 * np.pi * self.turns, self.num_points * 10)
        r_fine = (theta_fine / (2 * np.pi * self.turns)) * self.outer_radius

        # Compute differential arc lengths
        dx = np.diff(r_fine * np.cos(theta_fine))
        dy = np.diff(r_fine * np.sin(theta_fine))
        ds = np.sqrt(dx**2 + dy**2)
        s_cum = np.concatenate(([0], np.cumsum(ds)))

        # Total arc length
        s_total = s_cum[-1]

        # Desired equally spaced arc lengths
        s_uniform = np.linspace(0, s_total, self.num_points)

        # Interpolate theta for uniform spacing
        theta_uniform = np.interp(s_uniform, s_cum, theta_fine)
        r_uniform = (theta_uniform / (2 * np.pi * self.turns)) * self.outer_radius

        for r, t in zip(r_uniform, theta_uniform):
            x = int(self.center[0] + r * np.cos(t))
            y = int(self.center[1] + r * np.sin(t))
            self.path_points.append((x, y))


    def get_reference_dot(self, progress):
        """Get the position of the reference dot along the spiral path."""
        index = min(int(progress * (len(self.path_points) - 1)), len(self.path_points) - 1)
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
