import json
import unittest
from live_results import parse_live_results, evaluate_live_bets


class LiveTests(unittest.TestCase):
    def rows(self):
        return [dict(orden=n, temporada=2027, jornada=10, local='Local', visitante='Visitante',
                     local_goles='', visitante_goles='', estado='Sin comenzar', live=0, uts=1790707238)
                for n in range(1, 16)]

    def parse(self, rows):
        return parse_live_results(json.dumps(rows).encode(), '26-27', 10)

    def test_pending_zero_is_not_a_draw(self):
        rows = self.rows()
        rows[0].update(local_goles=0, visitante_goles=0)
        matches = self.parse(rows)
        self.assertEqual(matches[0].sign, '')
        score = evaluate_live_bets(['X'*14+'00'], matches)[0]
        self.assertEqual((score['hits'], score['known'], score['maximum'], score['pleno']), (0, 0, 14, 'Pendiente'))

    def test_live_final_and_pleno(self):
        rows = self.rows()
        rows[0].update(local_goles=0, visitante_goles=0, live=1, estado='Descanso')
        rows[1].update(local_goles=2, visitante_goles=1, estado='Finalizado')
        rows[14].update(local_goles=4, visitante_goles=2, live=1, estado='En juego')
        score = evaluate_live_bets(['X'*14+'M2'], self.parse(rows))[0]
        self.assertEqual((score['hits'], score['known'], score['fixed'], score['maximum']), (1, 2, 0, 13))
        self.assertEqual(score['pleno'], 'Sí (prov.)')
        rows[0].update(local_goles=1)
        self.assertEqual(evaluate_live_bets(['X'*14], self.parse(rows))[0]['hits'], 0)

    def test_rejects_wrong_round_season_and_duplicates(self):
        for field, value in [('jornada', 9), ('temporada', 2026), ('orden', 2)]:
            rows = self.rows()
            rows[0][field] = value
            with self.assertRaises(ValueError):
                self.parse(rows)

    def test_suspended_missing_and_unknown_states_are_not_results(self):
        for state in ('Suspendido', 'Aplazado', 'Desconocido'):
            rows = self.rows()
            rows[0].update(estado=state, local_goles=1, visitante_goles=0)
            self.assertEqual(self.parse(rows)[0].sign, '')
        rows[0].update(estado='En juego', live=1, local_goles=None)
        self.assertEqual(self.parse(rows)[0].sign, '')

    def test_final_results_and_drawn_sign(self):
        rows = self.rows()
        for row in rows:
            row.update(estado='Finalizado', local_goles=3, visitante_goles=0)
        score = evaluate_live_bets(['1'*14+'M0'], self.parse(rows))[0]
        self.assertEqual((score['hits'], score['fixed'], score['maximum'], score['pleno']), (14, 14, 14, 'Sí'))
        rows[0].update(estado='Suspendido', sorteado=1, signo='2')
        self.assertEqual(self.parse(rows)[0].sign, '2')


if __name__ == '__main__':
    unittest.main()
