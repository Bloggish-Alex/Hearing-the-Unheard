"""
Voice generator interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..model import Dataset, Note, Timing
from ..scales import Scale


@dataclass(frozen=True)
class VoiceContext:
    dataset: Dataset
    timing: Timing


class VoiceGenerator(ABC):
    """
    Turns a dataset into one voice's note stream according to declared voice in profile:

    Example:
    - id: 
        name: 
        generator: 
        series: 
        scale: 
        every: 
        duration_slots: []
        velocity: {base: , span: , floor: , ceiling: }
        skip_cadence_bar: true|false
    """

    def __init__(self,
                 voice_id: int,
                 series_id: str,
                 options: dict,
                 scale: Scale | None = None
                ):
        self.voice_id = voice_id
        self.series_id = series_id
        self.options = options
        self.scale = scale

    @abstractmethod
    def generate(self, ctx: VoiceContext) -> list[Note]:
        ...

    @staticmethod
    def velocity(value: float, scale: Scale, config: dict) -> int:
        x = (value - scale.lo) / (scale.hi - scale.lo)
        return int(
            max(
                config["floor"],
                min(config["ceiling"], config["base"] + x * config["span"])
            )
        )
