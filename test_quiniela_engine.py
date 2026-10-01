import math
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import MethodType, SimpleNamespace

from app import (
    Match, QuinielaApp, current_round, decode_pleno, evaluate_bets, parse_results,
    parse_scrutiny, quinielista_text, read_bet_file,
)
from data_updater import read_percentages

from quiniela_engine import (
    FilterConfig, coincidences, compose_probabilities, development_size,
    distances, filter_columns, generate_columns, interruptions, max_run,
    ProbabilitySource, reduce_columns,
)


class EngineTests(unittest.TestCase):
    def test_current_round_keeps_nearest_nominal_date(self):
        entries = [(10, date(2026, 9, 30)), (11, date(2026, 10, 4))]
        self.assertEqual(current_round(entries, date(2026, 10, 1)), 10)
        self.assertEqual(current_round(entries, date(2026, 10, 3)), 11)

    def test_scrutiny_and_bet_evaluation(self):
        prefix = "9 0 0 2 53 648 4639 108988,09 232507,92 54494,05 2056,38 168,19 28,19"
        line = prefix.ljust(104) + "12XX121112122XB" + "ABC" * 30 + " " * 24
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "PRE26-27.txt"
            path.write_text(line + "\n", encoding="latin-1")
            scrutiny = parse_scrutiny(path, 9)
        self.assertEqual(scrutiny["result"], "12XX121112122X")
        self.assertEqual(scrutiny["pleno"], "2M")
        self.assertEqual(scrutiny["prizes"][14], (0, 232507.92))
        bets = ["12XX121112122X2M", "12XX121112122X11", "22XX121112122X2M"]
        result = evaluate_bets(bets, scrutiny["result"], scrutiny["pleno"].replace("-", ""))
        self.assertEqual([item["category"] for item in result], [15, 14, 13])

    def test_read_exported_bets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bets.txt"
            path.write_text("1X211111111111M0\n2X1XXXXXXXXXXX11\n", encoding="utf-8")
            self.assertEqual(len(read_bet_file(path)), 2)
        self.assertEqual(decode_pleno("0"), "00")
        self.assertEqual(decode_pleno("F"), "MM")

    def test_quinielista_text_format(self):
        columns = ["1X2" + "1" * 11, tuple("2X1" + "X" * 11)]
        self.assertEqual(quinielista_text(columns, "M-0"), "1X211111111111M0\n2X1XXXXXXXXXXXM0\n")
        with self.assertRaises(ValueError):
            quinielista_text(["1X2"], "M-0")
        with self.assertRaises(ValueError):
            quinielista_text(columns, "")

    @staticmethod
    def sample_matches():
        return [
            Match(index, f"H{index}", f"A{index}", f"Local {index}", f"Visitante {index}", "", (60.0, 25.0, 15.0), "")
            for index in range(1, 16)
        ]

    def test_probable_columns_respect_selected_base(self):
        dummy = SimpleNamespace(matches=self.sample_matches())
        base = ["1X", "2"] + ["1"] * 12
        result = QuinielaApp.probable_columns(dummy, 20, base)
        self.assertEqual({column for column, _probability in result}, {"1" + "2" + "1" * 12, "X" + "2" + "1" * 12})

    def test_budget_optimizer_only_uses_existing_development(self):
        matches = self.sample_matches()
        source = ["1" * 14, "X" + "1" * 13, "2" + "1" * 13]
        dummy = SimpleNamespace(matches=matches)
        dummy._key = lambda match: str(match.number)
        dummy.predictions = {str(match.number): ("1X2" if match.number == 1 else "1") for match in matches[:14]}
        dummy.probable_columns = MethodType(QuinielaApp.probable_columns, dummy)
        plans = QuinielaApp.budget_plans(dummy, 1.50, source)
        self.assertTrue(plans)
        self.assertTrue(set(plans[0].columns) <= set(source))
        self.assertEqual(plans[0].bets, 2)

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
