"""Pruebas unitarias para la lógica de fechas y recurrencia de Acordate Bot."""

import unittest
from datetime import datetime, date
from src.handlers.add_debt import parse_flexible_date


class TestDateUtils(unittest.TestCase):
    def test_parse_flexible_date_full_format(self):
        res, err = parse_flexible_date("25/11/2026")
        self.assertIsNone(err)
        self.assertEqual(res, "2026-11-25")

    def test_parse_flexible_date_iso_format(self):
        res, err = parse_flexible_date("2026-12-15")
        self.assertIsNone(err)
        self.assertEqual(res, "2026-12-15")

    def test_parse_flexible_date_short_format(self):
        res, err = parse_flexible_date("28/11")
        self.assertIsNone(err)
        self.assertTrue(res.endswith("-11-28"))

    def test_parse_flexible_date_invalid(self):
        res, err = parse_flexible_date("fecha-invalida")
        self.assertIsNotNone(err)
        self.assertIsNone(res)

    def test_recurring_month_increment(self):
        try:
            from dateutil.relativedelta import relativedelta
            current_due = "2026-01-31"
            curr_date = datetime.strptime(current_due, "%Y-%m-%d").date()
            next_date = curr_date + relativedelta(months=1)
            self.assertEqual(next_date, date(2026, 2, 28))
        except ImportError:
            self.skipTest("dateutil no está instalado en el Python del sistema (se instalará vía requirements.txt).")


if __name__ == "__main__":
    unittest.main()
