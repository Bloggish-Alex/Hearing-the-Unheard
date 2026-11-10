"""
Pitch mappings.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scale:
    """
    Map a physical value onto a repeating pitch collection.
    """

    root: int
    steps: tuple[int, ...]
    lo: float
    hi: float
    max_degree: int

    def degree(self, value: float) -> int:
        """
        Maps a value to scale degree [0, max_degree]:
            1. normalize the value into [0, 1]
            2. scale to the degree range: x * max_degree
            3. round to the nearest integer
            4. clamp to [0, max_degree]

        Example (value = 0.45, steps = [0, 3, 5, 7, 10], lo = -0.6, hi = 1.5, max_degree = 10):
            1. normalize: 0.50
            2. scale to the degree range: 5.0
            3. round to the nearest integer: 5
            4. clamp to [0, max_degree]: 5
        """
        x = (value - self.lo) / (self.hi - self.lo)
        return max(0, min(self.max_degree, round(x * self.max_degree)))


    def midi(self, degree: int) -> int:
        """
        Maps degree to midi pitch value, the pitch value is in range of [57, 81] with default configuration in yaml.

        The quotient is "how many octaves up" and the remainder is "which node inside that octave".
        Example (root = 57, steps = [0, 3, 5, 7, 10]):
            degree = 7 -> divmod(7, 5) = (1, 2) -> 57 + 12 * 1 + steps[2] -> 57 + 12 + 5 = 74 (D5)
            degree = 10 -> divmod(10, 5) = (2, 0) -> 57 + 12 * 2 + steps[0] -> 57 + 24 + 0 = 81 (A5)
        """
        octave, step = divmod(degree, len(self.steps)) # (quotient, remainder)
        return self.root + 12 * octave + self.steps[step]
