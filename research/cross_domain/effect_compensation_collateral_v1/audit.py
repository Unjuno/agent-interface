from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

EXPECTED = {
    'correct': {
        'final': ('target', 'safe'),
        'events': [('effect', 'target', 'safe')],
        'outcome': 'EFFECT_VERIFIED',
        'primary_only': 'VERIFIED',
        'primary_only_truthful': True,
    },
    'wrong_compensated_clean': {
        'final': ('old', 'safe'),
        'events': [('effect', 'wrong', 'safe'), ('compensation', 'old', 'safe')],
        'outcome': 'EFFECT_CONTRADICTED_COMPENSATED',
        'primary_only': 'COMPENSATED',
        'primary_only_truthful': True,
    },
    'wrong_compensated_collateral': {
        'final': ('old', 'damaged'),
        'events': [('effect', 'wrong', 'safe'), ('compensation', 'old', 'damaged')],
        'outcome': 'EFFECT_CONTRADICTED_COMPENSATION_PARTIAL',
        'primary_only': 'COMPENSATED',
        'primary_only_truthful': False,
    },
    'wrong_uncompensated': {
        'final': ('wrong', 'safe'),
        'events': [('effect', 'wrong', 'safe')],
        'outcome': 'EFFECT_CONTRADICTED_UNCOMPENSATED',
        'primary_only': 'CONTRADICTED',
        'primary_only_truthful': True,
    },
}


def audit_case(case_dir: Path):
    recorded = json.loads((case_dir / 'result.json').read_text())
    db = case_dir / 'effect.sqlite'
    c = sqlite3.connect(db)
    final = c.execute('SELECT primary_value,collateral_value FROM state WHERE id=1').fetchone()
    events = [
        (r[1], r[2], r[3])
        for r in c.execute('SELECT seq,kind,primary_value,collateral_value,ns FROM events ORDER BY seq')
    ]
    event_ns = [
        r[0] for r in c.execute('SELECT ns FROM events ORDER BY seq')
    ]
    integrity = c.execute('PRAGMA integrity_check').fetchone()[0]
    c.close()

    expected = EXPECTED[recorded['scenario']]
    checks = {
        'integrity': integrity == 'ok',
        'final_state': tuple(final) == expected['final'],
        'events': events == expected['events'],
        'event_times_monotone': all(a <= b for a, b in zip(event_ns, event_ns[1:])),
        'outcome': recorded['outcome'] == expected['outcome'],
        'primary_only': recorded['primary_only_outcome'] == expected['primary_only'],
        'primary_restored': recorded['primary_restored'] == (final[0] == 'old'),
        'collateral_preserved': recorded['collateral_preserved'] == (final[1] == 'safe'),
        'full_restoration': recorded['full_restoration'] == (tuple(final) == ('old', 'safe')),
        'timestamps': (
            isinstance(recorded['started_ns'], int)
            and isinstance(recorded['finished_ns'], int)
            and recorded['started_ns'] <= recorded['finished_ns']
        ),
    }
    return {
        'id': recorded['id'],
        'scenario': recorded['scenario'],
        'checks': checks,
        'pass': all(checks.values()),
        'final_primary': final[0],
        'final_collateral': final[1],
        'events': events,
        'outcome': recorded['outcome'],
        'primary_only_outcome': recorded['primary_only_outcome'],
        'primary_only_truthful': expected['primary_only_truthful'],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    a = ap.parse_args()
    rows = []
    for d in sorted(a.root.iterdir()):
        if d.is_dir() and (d / 'result.json').exists():
            rows.append(audit_case(d))
    out = {
        'rows': rows,
        'count': len(rows),
        'all_pass': all(r['pass'] for r in rows),
        'primary_only_truthful_count': sum(r['primary_only_truthful'] for r in rows),
        'partial_compensation_count': sum(r['outcome'] == 'EFFECT_CONTRADICTED_COMPENSATION_PARTIAL' for r in rows),
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
