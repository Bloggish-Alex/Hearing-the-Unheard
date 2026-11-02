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
        x = (value - self.lo) / (self.hi - self.lo)
        return max(0, min(self.max_degree, round(x * self.max_degree)))

    def midi(self, degree: int) -> int:
        octave, step = divmod(degree, len(self.steps))
        return self.root + 12 * octave + self.steps[step]
