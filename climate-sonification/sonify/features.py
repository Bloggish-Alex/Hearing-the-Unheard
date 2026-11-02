"""
Per-bar signals computed from a Series.
"""

from __future__ import annotations

from statistics import mean, pstdev

from .model import Series


class Feature:
    """
    A new per-bar series from an existing one.

    Features represent bar-level values; intra-bar `slots` are not included.
    """

    slug = "feature"

    def compute(self, values: list[float | None]) -> list[float | None]:
        raise NotImplementedError

    def apply(self, series: Series, target: str | None = None) -> Series:
        return Series(
            id=target or f"{series.id}_{self.slug}",
            values=self.compute(series.values),
            label=f"{series.label} {self.slug}".strip(),
            unit=series.unit
        )


class OpDiff(Feature):
    slug = "diff"

    def compute(self, values: list[float | None]) -> list[float | None]:
        out: list[float | None] = [None]

        for previous, current in zip(values, values[1:]):
            out.append(None if previous is None or current is None else current - previous)

        return out


class OpAbsDiff(Feature):
    slug = "abs_diff"

    def compute(self, values: list[float | None]) -> list[float | None]:
        return [None if value is None else abs(value) for value in OpDiff().compute(values)]


class OpPctChange(Feature):
    slug = "pct_change"

    def compute(self, values: list[float | None]) -> list[float | None]:
        out: list[float | None] = [None]

        for previous, current in zip(values, values[1:]):
            if previous is None or current is None or previous == 0:
                out.append(None)
            else:
                out.append((current - previous) / abs(previous))

        return out


class OpRollingMean(Feature):
    slug = "rolling_mean"

    def __init__(self, window: int = 3):
        if window < 1:
            raise ValueError("Window must be at least 1")

        self.window = window

    def compute(self, values: list[float | None]) -> list[float | None]:
        out: list[float | None] = []

        for index in range(len(values)):
            start = index - self.window + 1

            if start < 0:
                out.append(None)
                continue

            window = values[start : index + 1]
            present = [value for value in window if value is not None]
            out.append(mean(present) if len(present) == self.window else None)

        return out


class OpRollingStd(Feature):
    slug = "rolling_std"

    def __init__(self, window: int = 3):
        if window < 1:
            raise ValueError("Window must be at least 1")

        self.window = window

    def compute(self, values: list[float | None]) -> list[float | None]:
        out: list[float | None] = []

        for index in range(len(values)):
            start = index - self.window + 1

            if start < 0:
                out.append(None)
                continue

            window = values[start : index + 1]
            present = [value for value in window if value is not None]
            out.append(pstdev(present) if len(present) == self.window else None)

        return out


class OpDrawdown(Feature):
    slug = "drawdown"

    def compute(self, values: list[float | None]) -> list[float | None]:
        peak: float | None = None
        out: list[float | None] = []

        for value in values:
            if value is None:
                out.append(None)
                continue

            peak = value if peak is None else max(peak, value)
            out.append((value - peak) / abs(peak) if peak else 0.0)

        return out


FEATURES: dict[str, type[Feature]] = {
    "diff": OpDiff,
    "abs_diff": OpAbsDiff,
    "pct_change": OpPctChange,
    "rolling_mean": OpRollingMean,
    "rolling_std": OpRollingStd,
    "drawdown": OpDrawdown
}
