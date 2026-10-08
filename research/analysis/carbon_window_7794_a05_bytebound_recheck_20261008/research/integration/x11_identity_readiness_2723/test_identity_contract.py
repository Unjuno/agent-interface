from identity_contract import audit_captures


def test_requires_all_apps_and_typed_stable_distinct_records() -> None:
    first = [
        {'app': 'inkscape', 'window_id': 11, 'pid': 101, 'title': 'Inkscape', 'wm_class': 'Inkscape'},
        {'app': 'libreoffice', 'window_id': 12, 'pid': 102, 'title': 'Calc', 'wm_class': 'LibreOffice'},
        {'app': 'chromium', 'window_id': 13, 'pid': 103, 'title': 'Chromium', 'wm_class': 'Chromium'},
    ]
    second = [dict(row) for row in first]
    result = audit_captures(first, second, {'inkscape', 'libreoffice', 'chromium'})
    assert result['decision'] == 'PASS_IDENTITY_READINESS'
    assert result['stable'] is True


def test_reports_missing_app_and_field() -> None:
    first = [{'app': 'chromium', 'window_id': 13, 'pid': 103, 'title': 'Chromium', 'wm_class': ''}]
    result = audit_captures(first, first, {'inkscape', 'libreoffice', 'chromium'})
    assert result['decision'] == 'HOLD_IDENTITY_DISCOVERY'
    assert 'inkscape' in result['missing_apps']
    assert 'wm_class' in result['missing_fields']
