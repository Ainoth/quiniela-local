import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app
import data_updater


def percentages_xml(season=2027, number=12, values=(50, 30, 20)):
    return ('<quinielista><porcentajes temporada="%s" jornada="%s">' % (season, number) + ''.join(
        '<partido num="%s" p_jugados_1="%s" p_jugados_X="%s" p_jugados_2="%s"/>' % (n, *values)
        for n in range(1, 16)) + '</porcentajes></quinielista>').encode()


class DataTests(unittest.TestCase):
    def test_public_percentages_validate_identity_and_values(self):
        self.assertEqual(data_updater._validated_percentages(percentages_xml(), "26-27", 12)[0], (50, 30, 20))
        for xml in (percentages_xml(number=11), percentages_xml(season=2026), percentages_xml(values=(-10, 50, 60)), percentages_xml(values=(float("nan"), 50, 50))):
            with self.assertRaises(ValueError):
                data_updater._validated_percentages(xml, "26-27", 12)

    def test_bad_download_preserves_previous_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "porcentajes_26-27_J12.xml"
            path.write_bytes(percentages_xml())
            with patch.object(data_updater, "_download", return_value=percentages_xml(number=11)):
                with self.assertRaises(ValueError):
                    data_updater.fetch_percentages("26-27", 12, Path(tmp))
            self.assertEqual(path.read_bytes(), percentages_xml())

    def test_pre_fixed_field_and_accumulated_categories(self):
        # Jornada 10 pegada al primer número de acertantes.
        line = "100 2 3 4 5 6 200,00 100,00 50,00 20,00 5,00 2,00".ljust(104) + "1"*14 + "0" + "ABCDEF"*15
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PRE26-27.TXT"
            path.write_text(line)
            s = app.parse_scrutiny(path, 10)
            with patch.object(app, "DATA", Path(tmp)):
                self.assertEqual(len(app.parse_round_teams("26-27", 10)), 15)
        self.assertEqual(s["prizes"][14], (2, 100))
        row = app.evaluate_bets(["1"*14+"00"], s["result"], s["pleno"])[0]
        self.assertEqual(row["categories"], [14, 15])
        self.assertEqual(sum(s["prizes"][c][1] for c in row["categories"]), 300)


if __name__ == "__main__":
    unittest.main()
