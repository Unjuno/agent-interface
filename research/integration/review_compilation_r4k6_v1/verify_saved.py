"""Restore and audit saved records. Never invoke run_once or native actions."""
import json
from pathlib import Path
from audit import audit
from controls import controls
from io_data import inputs, load_packed

HERE = Path(__file__).resolve().parent


def main():
    records = load_packed(HERE / 'records.b64', json.loads((HERE / 'RECORDS.json').read_text()))
    cases = inputs(HERE)
    freeze = json.loads((HERE / 'FREEZE.json').read_text())['files']
    measured = audit(records, cases, freeze)
    challenged = controls(records, cases, freeze)
    if measured != json.loads((HERE / 'AUDIT.json').read_text()):
        raise ValueError('saved audit does not reproduce')
    if challenged != json.loads((HERE / 'CONTROLS.json').read_text()):
        raise ValueError('saved controls do not reproduce')
    if measured['errors'] or challenged['rejected'] != 8:
        raise ValueError('retained gate did not pass')
    print(json.dumps({'status': 'PASS_SAVED_RECORD_RECONSTRUCTION',
                      'records': len(records['rows']), 'controls': 8,
                      'new_matrix_runs': 0, 'new_gui_runs': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
