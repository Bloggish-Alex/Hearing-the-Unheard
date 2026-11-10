"""
Domain-neutral score model:

Maps time series into bars, one bar = one period (year, month, quarter or week)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Note:
    tick: int
    dur: int
    midi: int
    vel: int
    voice: int
    art: int = 0  # articulation: -1 staccato, 0 normal (climate velocity -> attack)


@dataclass(frozen=True)
class Period:
    """
    One musical bar, labelled and placed on the source time axis.
    """

    label: str
    start: float
    end: float


@dataclass(frozen=True)
class Series:
    """
    One value per bar, with optional intra-bar detail in `slots`.
    """

    id: str
    values: list[float | None]
    label: str = ""
    unit: str = ""
    slots: list[list[float | None]] | None = None


@dataclass(frozen=True)
class Annotation:
    """
    A point on the source time axis as marker in the presentation.
    """

    at: float
    label: str


@dataclass(frozen=True)
class Timing:
    """
    Musical clock used by the composer and renderers.
    """

    ticks_per_quarter: int
    eighth: int
    bar_ticks: int
    section_bars: int


@dataclass(frozen=True)
class Section:
    label: str
    start: int
    end: int
    anchor: float | None = None
    mean: float | None = None


@dataclass
class Dataset:
    """
    Parsed input data, before any musical mapping.
    """

    periods: list[Period]
    series: dict[str, Series]
    sections: list[Section] = field(default_factory=list)
    annotations: list[Annotation] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


@dataclass
class Voice:
    id: int
    label: str
    notes: list[Note]


@dataclass
class Composition:
    """
    Generated score: note streams, tempo map, and form metadata.
    """

    voices: list[Voice]
    tempo_map: list[tuple[int, int]]
    n_bars: int
    sections: list[Section] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    @property
    def notes(self) -> list[Note]:
        """
        All voice notes in voice order.
        """
        return [note for voice in self.voices for note in voice.notes]

    def bar_times(self) -> tuple[list[float], float]:
        """
        Start time of bar and the total duration (in seconds).
        """
        times = []
        t = 0.0
        idx = 0
        bpm = self.tempo_map[0][1]

        for bar in range(self.n_bars):
            while idx + 1 < len(self.tempo_map) and self.tempo_map[idx + 1][0] <= bar:
                idx += 1
                bpm = self.tempo_map[idx][1]

            times.append(t)    
            t += 240.0 / bpm  # 12 eighths per bar

        return times, t
