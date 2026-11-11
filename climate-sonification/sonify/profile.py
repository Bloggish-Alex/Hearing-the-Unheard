"""
Profiles: declarative mapping from a dataset to a score.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .model import Timing
from .scales import Scale


@dataclass(frozen=True)
class VoiceSpec:
    id: int
    name: str
    generator: str
    series: str
    scale: str | None
    options: dict


@dataclass(frozen=True)
class Profile:
    """
    Parse from a yaml file which contains declarative mapping information on
    how data is mapped into score or music elements
    """
    name: str
    title: str
    directory: Path
    start_year: int
    end_year: int
    timing: Timing
    scales: dict[str, Scale]
    voices: list[VoiceSpec]

    @classmethod
    def load(cls, path: Path) -> Profile:
        path = Path(path)
        raw = yaml.safe_load(path.read_text())

        data = raw["data"]
        timing = Timing(**raw["timing"])

        scales = {
            name: Scale(
                root=spec["root"],
                steps=tuple(spec["steps"]),
                lo=spec["lo"],
                hi=spec["hi"],
                max_degree=spec["max_degree"],
            )
            for name, spec in raw["scales"].items()
        }

        reserved = {"id", "name", "generator", "series", "scale"}
        voices = [
            VoiceSpec(
                id=voice["id"],
                name=voice["name"],
                generator=voice["generator"],
                series=voice["series"],
                scale=voice.get("scale"),
                options={
                    key: value for key, value in voice.items() if key not in reserved                    
                },
            )
            for voice in raw["voices"]
        ]

        return cls(
            name=raw["name"],
            title=raw["title"],
            directory=(path.parent / data["directory"]).resolve(),
            start_year=data["start_year"],
            end_year=data["end_year"],
            timing=timing,
            scales=scales,
            voices=voices
        )
