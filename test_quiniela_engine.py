import math
import tempfile
import unittest
from pathlib import Path

from app import parse_results
from data_updater import read_percentages

from quiniela_engine import (
    FilterConfig, coincidences, compose_probabilities, development_size,
    distances, filter_columns, generate_columns, interruptions, max_run,
    ProbabilitySource, reduce_columns,
)


class EngineTests(unittest.TestCase):
    def test_cached_percentages(self):
        xml = b'''<?xml version="1.0"?><quinielista><porcentajes>''' + b"".join(
            f'<partido num="{number}" p_jugados_1="50" p_jugados_X="30" p_jugados_2="20"/>'.encode()
            for number in range(1, 16)
        ) + b'''</porcentajes></quinielista>'''
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "porcentajes_26-27_J10.xml").write_bytes(xml)
            values = read_percentages("26-27", 10, Path(directory))
            self.assertEqual(values[0], (50.0, 30.0, 20.0))

    def test_win1x2_result_record_format(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.txt"
            path.write_text("0101ALAGET3020260201ATBSEV  2026", encoding="ascii")
            self.assertEqual(parse_results(path, 3), [("ALA", "GET", 3, 0)])

    def test_cartesian_base(self):
        base = [("1", "X"), ("1",), ("1", "X", "2")]
        self.assertEqual(development_size(base), 6)
        self.assertEqual(len(list(generate_columns(base))), 6)

    def test_basic_conditions(self):
        columns = generate_columns([("1", "X", "2")] * 4)
        config = FilterConfig(variants=(2, 2), x_count=(1, 1), two_count=(1, 1), max_runs={"1": 2})
        result = list(filter_columns(columns, config))
        self.assertTrue(result)
        self.assertTrue(all(column.count("X") == 1 and column.count("2") == 1 for column in result))

    def test_sequence_metrics(self):
        column = tuple("111XX22211")
        self.assertEqual(max_run(column, "1"), 3)
        self.assertEqual(interruptions(column), 3)
        self.assertEqual(distances(column, "X"), (1,))
        self.assertEqual(coincidences(column, tuple("111XX22212")), 9)

    def test_weighted_probability_source(self):
        sources = {
            "A": ProbabilitySource("A", ((0.6, 0.3, 0.1),)),
            "B": ProbabilitySource("B", ((0.2, 0.3, 0.5),)),
        }
        result = compose_probabilities(sources, {"A": 0.25, "B": 0.75})
        self.assertTrue(math.isclose(result[0][0], 0.3))
        self.assertTrue(math.isclose(result[0][2], 0.4))

    def test_reduction_is_unique_and_bounded(self):
        columns = list(generate_columns([("1", "X", "2")] * 3))
        reduced = reduce_columns(columns, 5)
        self.assertEqual(len(reduced), 5)
        self.assertEqual(len(set(reduced)), 5)


if __name__ == "__main__":
    unittest.main()
