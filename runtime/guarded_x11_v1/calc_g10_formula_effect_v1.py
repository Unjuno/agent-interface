"""Pure saved-FODS effect scoring for the retained G10 formula task.

This module scores bytes only. It does not establish that Calc saved them,
that a task controller owned the artifact, or that task_success is true.
Those claims require the parent-held call/target/save custody path.
"""
import xml.etree.ElementTree as ET


_NS = {
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
}
_MAX_BYTES = 64 * 1024 * 1024
_MAX_REPEAT = 1_000_000


def _expected_populated(a, b):
    if (type(a) is not int or type(b) is not int
            or (a, b) not in ((29, 31), (43, 47))):
        raise ValueError('values must match one of the two retained G10 cases')
    product = a * b
    return [
        (0, 0, 'a', None, None),
        (0, 1, 'b', None, None),
        (0, 2, 'product', None, None),
        (1, 0, str(a), str(a), None),
        (1, 1, str(b), str(b), None),
        (1, 2, str(product), str(product), 'of:=[.A2]*[.B2]'),
    ]


def score_g10_fods_bytes(data, *, a, b):
    """Return whether bytes encode the exact G10 header, values and formula.

    A mismatch is a negative effect result; malformed, ambiguous, oversized,
    or unsupported XML is unknown. `task_success` is deliberately always None.
    """
    expected = _expected_populated(a, b)
    if (not isinstance(data, bytes) or not data or len(data) > _MAX_BYTES
            or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper()):
        return {'status': 'unknown', 'effect_match': None,
                'task_success': None, 'reason': 'artifact_unavailable_or_unsafe'}
    try:
        root = ET.fromstring(data)
        sheets = root.findall(
            './/office:body/office:spreadsheet/table:table', _NS)
        if len(sheets) != 1:
            raise ValueError('sheet_count_ambiguous')
        sheet = sheets[0]
        if sheet.find('.//table:covered-table-cell', _NS) is not None:
            raise ValueError('covered_cells_unsupported')
        populated = []
        row_index = 0
        for row in sheet.findall('table:table-row', _NS):
            row_repeat = int(row.get(
                '{%s}number-rows-repeated' % _NS['table'], '1'))
            if not 1 <= row_repeat <= _MAX_REPEAT:
                raise ValueError('row_repeat_out_of_bounds')
            column_index = 0
            for cell in row.findall('table:table-cell', _NS):
                column_repeat = int(cell.get(
                    '{%s}number-columns-repeated' % _NS['table'], '1'))
                if not 1 <= column_repeat <= _MAX_REPEAT:
                    raise ValueError('column_repeat_out_of_bounds')
                text = ''.join(cell.itertext()).strip()
                value = cell.get('{%s}value' % _NS['office'])
                formula = cell.get('{%s}formula' % _NS['table'])
                if text or value is not None or formula is not None:
                    if row_repeat != 1 or column_repeat != 1:
                        raise ValueError('repeated_populated_cell_unsupported')
                    populated.append((row_index, column_index, text,
                                      value, formula))
                column_index += column_repeat
            row_index += row_repeat
        matched = populated == expected
        return {'status': 'verified' if matched else 'mismatch',
                'effect_match': matched, 'task_success': None,
                'expected_populated': expected,
                'observed_populated': populated}
    except (ET.ParseError, TypeError, ValueError, OverflowError) as error:
        return {'status': 'unknown', 'effect_match': None,
                'task_success': None,
                'reason': str(error) or type(error).__name__}
