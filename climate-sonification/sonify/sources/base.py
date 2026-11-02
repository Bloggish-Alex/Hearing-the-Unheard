"""
Interfaces that produces a dataset
"""

from __future__ import annotations

from typing import Protocol

from ..model import Dataset


class DataSource(Protocol):
    """
    Anything that can produce a Dataset.
    """

    def load(self) -> Dataset:
        ...
