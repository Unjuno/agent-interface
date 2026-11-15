import unittest
from pathlib import Path

from runtime.guarded_x11_v1.calc_g10_formula_effect_v1 import (
    score_g10_fods_bytes,
)


NS = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
      'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
      'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"')


def fods(*, a='29', b='31', product='899', formula='of:=[.A2]*[.B2]',
         extra=''):
    return (f'<office:document {NS}><office:body><office:spreadsheet>'
            '<table:table table:name="Sheet1">'
            '<table:table-row>'
            '<table:table-cell><text:p>a</text:p></table:table-cell>'
            '<table:table-cell><text:p>b</text:p></table:table-cell>'
            '<table:table-cell><text:p>product</text:p></table:table-cell>'
            '</table:table-row><table:table-row>'
            f'<table:table-cell office:value="{a}" office:value-type="float">'
            f'<text:p>{a}</text:p></table:table-cell>'
            f'<table:table-cell office:value="{b}" office:value-type="float">'
            f'<text:p>{b}</text:p></table:table-cell>'
            f'<table:table-cell table:formula="{formula}" '
            f'office:value="{product}" office:value-type="float">'
            f'<text:p>{product}</text:p></table:table-cell>{extra}'
            '</table:table-row></table:table>'
            '</office:spreadsheet></office:body></office:document>').encode()


class CalcG10FormulaEffectTests(unittest.TestCase):
    def test_archived_g10_saved_bytes_match_their_registered_formula_cases(self):
        root = (Path(__file__).resolve().parents[2] / 'research' / 'integration'
                / 'calc_current_shared_3311_4d74_20261004'
                / 'calc-compiled-ocrlive-4d74' / 'runs' / 'compiled_ocrlive10')
        for name, a, b in (('first.fods', 29, 31),
                           ('second.fods', 43, 47)):
            result = score_g10_fods_bytes((root / name).read_bytes(), a=a, b=b)
            self.assertEqual(result['status'], 'verified', name)
            self.assertIsNone(result['task_success'], name)

    def test_retained_g10_formula_cases_are_scored(self):
        for a, b in ((29, 31), (43, 47)):
            result = score_g10_fods_bytes(
                fods(a=str(a), b=str(b), product=str(a * b)), a=a, b=b)
            self.assertEqual(result['status'], 'verified')
            self.assertIs(result['effect_match'], True)
            self.assertIsNone(result['task_success'])

    def test_cached_result_and_exact_formula_are_both_required(self):
        self.assertEqual(score_g10_fods_bytes(
            fods(product='900'), a=29, b=31)['status'], 'mismatch')
        self.assertEqual(score_g10_fods_bytes(
            fods(formula='of:=[.A2]+[.B2]'), a=29, b=31)['status'], 'mismatch')

    def test_extra_populated_cell_fails_closed_as_mismatch(self):
        extra = ('<table:table-cell office:value="7" '
                 'office:value-type="float"><text:p>7</text:p>'
                 '</table:table-cell>')
        result = score_g10_fods_bytes(fods(extra=extra), a=29, b=31)
        self.assertEqual(result['status'], 'mismatch')
        self.assertIsNone(result['task_success'])

    def test_unsafe_or_malformed_xml_is_unknown(self):
        for data in (b'<!DOCTYPE x [<!ENTITY e "x">]><x/>', b'<broken'):
            result = score_g10_fods_bytes(data, a=29, b=31)
            self.assertEqual(result['status'], 'unknown')
            self.assertIsNone(result['effect_match'])
            self.assertIsNone(result['task_success'])

    def test_invalid_expected_values_are_rejected(self):
        for a, b in ((True, 1), (-1, 1), (1, 1.0), (1_000_000_000, 1),
                     (29, 32)):
            with self.assertRaises(ValueError):
                score_g10_fods_bytes(b'<x/>', a=a, b=b)


if __name__ == '__main__':
    unittest.main()
