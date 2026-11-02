from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sonify.model import Composition, Note, Voice
from sonify.scales import Scale

PENTA = (0, 3, 5, 7, 10)


class ScaleTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temperature = Scale(57, PENTA, -0.6, 1.5, 10)

    def test_degree_clamps_to_range(self) -> None:
        self.assertEqual(self.temperature.degree(-2.0), 0)
        self.assertEqual(self.temperature.degree(5.0), 10)

    def test_degree_rounds_to_nearest(self) -> None:
        self.assertEqual(self.temperature.degree(-0.6), 0)
        self.assertEqual(self.temperature.degree(0.45), 5)

    def test_midi_repeats_pentatonic_per_octave(self) -> None:
        self.assertEqual(self.temperature.midi(0), 57)
        self.assertEqual(self.temperature.midi(5), 69)
        self.assertEqual(self.temperature.midi(10), 81)

    def test_non_repeating_scale(self) -> None:
        co2 = Scale(50, (0, 2, 3, 5, 7, 9, 10, 12), 315.0, 425.0, 7)
        self.assertEqual(co2.degree(315.0), 0)
        self.assertEqual(co2.degree(425.0), 7)
        self.assertEqual(co2.midi(7), 62)


class CompositionTest(unittest.TestCase):

    def test_notes_flatten_voices_in_order(self) -> None:
        melody = Note(0, 10, 60, 80, 0)
        bass = Note(10, 10, 62, 70, 1)
        composition = Composition(
            voices=[Voice(0, "melody", [melody]), Voice(1, "bass", [bass])],
            tempo_map=[(0, 60)],
            n_bars=1,
        )
        self.assertEqual(composition.notes, [melody, bass])

    def test_bar_times_follow_tempo_map(self) -> None:
        composition = Composition(
            voices=[],
            tempo_map=[(0, 60), (2, 120)],
            n_bars=4,
        )
        times, total = composition.bar_times()
        self.assertEqual(times, [0.0, 4.0, 8.0, 10.0])
        self.assertEqual(total, 12.0)

    def test_note_articulation_defaults_to_normal(self) -> None:
        self.assertEqual(Note(0, 1, 60, 80, 0).art, 0)


if __name__ == "__main__":
    unittest.main()
