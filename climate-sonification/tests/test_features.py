from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sonify.features import OpAbsDiff, OpDiff, OpDrawdown, OpPctChange, OpRollingMean, OpRollingStd
from sonify.model import Series


class FeatureTest(unittest.TestCase):
    def test_diff(self) -> None:
        self.assertEqual(OpDiff().compute([1.0, 3.0, 6.0]), [None, 2.0, 3.0])

    def test_diff_propagates_gaps(self) -> None:
        self.assertEqual(OpDiff().compute([1.0, None, 3.0]), [None, None, None])

    def test_abs_diff(self) -> None:
        self.assertEqual(OpAbsDiff().compute([1.0, 3.0, 2.0]), [None, 2.0, 1.0])

    def test_pct_change(self) -> None:
        self.assertEqual(OpPctChange().compute([100.0, 110.0]), [None, 0.1])

    def test_pct_change_skips_zero(self) -> None:
        self.assertEqual(OpPctChange().compute([0.0, 1.0]), [None, None])

    def test_rolling_mean_requires_full_window(self) -> None:
        self.assertEqual(OpRollingMean(2).compute([1.0, 2.0, 3.0]), [None, 1.5, 2.5])

    def test_rolling_mean_handles_gaps(self) -> None:
        self.assertEqual(OpRollingMean(2).compute([1.0, None, 3.0]), [None, None, None])

    def test_rolling_std(self) -> None:
        self.assertEqual(OpRollingStd(2).compute([1.0, 3.0, 3.0]), [None, 1.0, 0.0])

    def test_rolling_rejects_empty_window(self) -> None:
        with self.assertRaises(ValueError):
            OpRollingMean(0)

    def test_drawdown(self) -> None:
        values = OpDrawdown().compute([100.0, 120.0, 90.0, 100.0])
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[1], 0.0)
        self.assertAlmostEqual(values[2], -0.25)
        self.assertAlmostEqual(values[3], -1 / 6)

    def test_apply_names_target_and_keeps_unit(self) -> None:
        series = Series(id="temp", values=[1.0, 3.0], label="Temp", unit="°C")
        derived = OpDiff().apply(series)
        self.assertEqual(derived.id, "temp_diff")
        self.assertEqual(derived.values, [None, 2.0])
        self.assertEqual(derived.unit, "°C")


if __name__ == "__main__":
    unittest.main()
