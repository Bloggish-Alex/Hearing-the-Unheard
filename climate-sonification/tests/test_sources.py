from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sonify.sources import ClimateSource, CsvTable


def gistemp_csv(years: list[int]) -> str:
    lines = ["Year,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec,J-D"]
    for offset, year in enumerate(years):
        months = ",".join(str(float(offset + month)) for month in range(12))
        lines.append(f"{year},{months},0.0")
    return "\n".join(lines) + "\n"


def co2_csv() -> str:
    return "\n".join(
        [
            "# synthetic NOAA fixture",
            "year,month,decimal date,average,deseasonalized,ndays,sdev,unc",
            "2000,1,2000.042,369.0,368.0,31,0.1,0.1",
            "2000,2,2000.125,370.0,370.0,29,0.1,0.1",
            "2001,1,2001.042,371.0,371.0,31,0.1,0.1",
        ]
    ) + "\n"


def hemispheric_csv(value: float, years: list[int]) -> str:
    lines = ["Year,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec,J-D"]
    months = ",".join([str(value)] * 12)
    for year in years:
        lines.append(f"{year},{months},0.0")
    return "\n".join(lines) + "\n"


class ClimateSourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        (self.directory / "gistemp.csv").write_text(gistemp_csv([2000, 2001]))
        (self.directory / "co2_mm_mlo.csv").write_text(co2_csv())
        (self.directory / "gistemp_nh.csv").write_text(hemispheric_csv(1.5, [2000, 2001]))
        (self.directory / "gistemp_sh.csv").write_text(hemispheric_csv(0.5, [2000, 2001]))
        self.dataset = ClimateSource(self.directory, 2000, 2001).load()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_periods_are_years(self) -> None:
        self.assertEqual([p.label for p in self.dataset.periods], ["2000", "2001"])
        self.assertEqual([p.start for p in self.dataset.periods], [2000.0, 2001.0])
        self.assertEqual([p.end for p in self.dataset.periods], [2001.0, 2002.0])

    def test_temperature_series_keeps_monthly_slots(self) -> None:
        temp = self.dataset.series["temp"]
        self.assertEqual(temp.values, [5.5, 6.5])
        self.assertEqual(temp.slots[0], [float(i) for i in range(12)])
        self.assertEqual(temp.slots[1], [float(i) for i in range(1, 13)])
        self.assertEqual(temp.unit, "°C")

    def test_co2_is_annual_mean(self) -> None:
        self.assertEqual(self.dataset.series["co2"].values, [369.0, 371.0])
        self.assertEqual(self.dataset.meta["co2_start_year"], 2000)

    def test_contrast_is_nh_minus_sh(self) -> None:
        self.assertEqual(self.dataset.series["contrast"].values, [1.0, 1.0])

    def test_co2_entry_annotation(self) -> None:
        self.assertEqual(len(self.dataset.annotations), 1)
        self.assertEqual(self.dataset.annotations[0].at, 2000.0)
        self.assertEqual(self.dataset.annotations[0].label, "CO₂ enters")

    def test_co2_entry_follows_requested_range(self) -> None:
        dataset = ClimateSource(self.directory, 2001, 2001).load()
        self.assertEqual(dataset.meta["co2_start_year"], 2000)
        self.assertEqual(dataset.meta["co2_entry_year"], 2001)
        self.assertEqual(dataset.annotations[0].at, 2001.0)

    def test_missing_optional_sources_become_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "gistemp.csv").write_text(gistemp_csv([2000]))
            dataset = ClimateSource(directory, 2000, 2000).load()
        self.assertEqual(dataset.series["co2"].values, [None])
        self.assertEqual(dataset.series["contrast"].values, [None])
        self.assertEqual(dataset.annotations, [])
        self.assertIsNone(dataset.meta["co2_start_year"])

    def test_empty_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            ClimateSource(self.directory, 1990, 1991).load()


class CsvTableTest(unittest.TestCase):
    def test_finds_header_after_preamble(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "table.csv"
            path.write_text("# note\nname,value\na,1\n")
            table = CsvTable(path, "name")
            self.assertEqual(table.dict_rows(), [{"name": "a", "value": "1"}])


class RepoDataTest(unittest.TestCase):
    def test_committed_snapshot_loads(self) -> None:
        dataset = ClimateSource(ROOT / "data", 1925, 2024).load()
        self.assertEqual(len(dataset.periods), 100)
        self.assertEqual(dataset.meta["start_year"], 1925)
        self.assertEqual(dataset.meta["co2_start_year"], 1958)
        self.assertEqual(dataset.meta["co2_entry_year"], 1958)
        self.assertEqual(len(dataset.series["temp"].slots[0]), 12)
        self.assertIsNotNone(dataset.series["temp"].values[-1])


if __name__ == "__main__":
    unittest.main()
