"""
NASA GISTEMP and NOAA Mauna Loa climate data sources.
"""

from __future__ import annotations

from pathlib import Path

from ..model import Annotation, Dataset, Period, Series
from .csv_table import CsvTable

TEMPERATURE_FILE = "gistemp.csv"
CO2_FILE = "co2_mm_mlo.csv"
NH_TEMPERATURE_FILE = "gistemp_nh.csv"
SH_TEMPERATURE_FILE = "gistemp_sh.csv"

GISTEMP_HEADER = "Year"
CO2_HEADER = "year"


class ClimateSource:
    """
    Load the GISTEMP / Mauna Loa snapshots into a Dataset.

    One year is mapped into one bar. The temperature series keeps its twelve monthly
    values in `slots`; CO2 and hemispheric contrast are annual series.
    """

    def __init__(self, directory: Path, start_year: int, end_year: int):
        self.directory = Path(directory)
        self.start_year = start_year
        self.end_year = end_year

    def load(self) -> Dataset:
        temperatures = self.load_temperatures(self.directory / TEMPERATURE_FILE)
        co2 = self.load_co2(self.directory / CO2_FILE)
        contrast = self.load_contrast(self.directory / NH_TEMPERATURE_FILE,
                                      self.directory / SH_TEMPERATURE_FILE)

        rows = [(year, months) for year, months in temperatures if self.start_year <= year <= self.end_year]

        if not rows:
            raise ValueError("No temperature data.")

        periods = [Period(label=str(year), start=float(year), end=float(year + 1)) for year, _ in rows]

        series = {
            "temp": Series(
                id="temp",
                values=[sum(months) / len(months) for _, months in rows],
                label="Temperature anomaly",
                unit="°C",
                slots=[months for _, months in rows]
            ),
            "co2": Series(
                id="co2",
                values=[co2.get(year) for year, _ in rows],
                label="CO₂",
                unit="ppm"
            ),
            "contrast": Series(
                id="contrast",
                values=[contrast.get(year) for year, _ in rows],
                label="NH−SH contrast",
                unit="°C"
            )
        }

        co2_start = min(co2) if co2 else None
        co2_entry = next(
            (
                year for year, _ in rows if co2_start is not None and year >= co2_start and year in co2
            ),
            None
        )

        annotations = []
        if co2_entry is not None:
            annotations.append(Annotation(at=float(co2_entry), label="CO₂ enters"))

        return Dataset(
            periods=periods,
            series=series,
            annotations=annotations,
            meta={
                "start_year": rows[0][0],
                "end_year": rows[-1][0],
                "co2_start_year": co2_start,
                "co2_entry_year": co2_entry
            }
        )


    @staticmethod
    def load_temperatures(path: Path) -> list[tuple[int, list[float]]]:
        """
        Return (year, [Jan...Dec values]) for complete years only.

        Year is skipped when any of its twelve months is missing ('***' or blank).
        """
        table = CsvTable(path, GISTEMP_HEADER)
        out = []

        for row in table.data_rows():
            if not row or not row[0].strip().isdigit():
                continue

            parsed: list[float | None] = []

            for cell in row[1:13]:
                cell = cell.strip()
                parsed.append(float(cell) if cell not in ("***", "") else None)

            if len(parsed) == 12 and all(value is not None for value in parsed):
                out.append(
                    (int(row[0]), [value for value in parsed if value is not None])
                )

        return out


    @staticmethod
    def load_co2(path: Path) -> dict[int, float]:
        """
        Annual mean of NOAA's deseasonalized monthly Mauna Loa CO2.

        Return (year, mean of monthly value).
        """

        if not path.exists():
            return {}

        table = CsvTable(path, CO2_HEADER)
        months: dict[int, list[float]] = {}

        for row in table.dict_rows():
            year = row.get("year", "").strip()

            if not year.isdigit():
                continue

            try:
                value = float(row["deseasonalized"])
            except (KeyError, ValueError):
                continue

            months.setdefault(int(year), []).append(value)

        return {year: sum(values) / len(values) for year, values in months.items() if values}


    def load_contrast(self, nh_path: Path, sh_path: Path) -> dict[int, float]:
        """
        Annual NH minus SH anomaly contrast; {} if the tables are absent.
        """
        if not nh_path.exists() or not sh_path.exists():
            return {}

        north = dict(self.load_temperatures(nh_path))
        south = dict(self.load_temperatures(sh_path))

        return {
            year: sum(a - b for a, b in zip(north[year], south[year])) / 12 for year in north.keys() & south.keys()
        }
