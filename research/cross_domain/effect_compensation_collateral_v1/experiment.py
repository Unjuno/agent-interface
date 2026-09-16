from __future__ import annotations
import argparse, json, sqlite3, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECEIVER = ROOT / 'receiver.py'
INITIAL_PRIMARY = 'old'
INITIAL_COLLATERAL = 'safe'
INTENDED_PRIMARY = 'target'


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def run_receiver(db: Path, kind: str, primary: str, collateral: str):
    p = subprocess.run(
        [sys.executable, str(RECEIVER), str(db), kind, primary, collateral],
        text=True, capture_output=True
    )
    if p.returncode != 0:
        raise RuntimeError((p.returncode, p.stdout, p.stderr))
    return {'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def read_db(db: Path):
    c = sqlite3.connect(db)
    primary, collateral = c.execute(
        'SELECT primary_value,collateral_value FROM state WHERE id=1'
    ).fetchone()
    events = [
        {'seq': r[0], 'kind': r[1], 'primary': r[2], 'collateral': r[3], 'ns': r[4]}
        for r in c.execute(
            'SELECT seq,kind,primary_value,collateral_value,ns FROM events ORDER BY seq'
        )
    ]
    integrity = c.execute('PRAGMA integrity_check').fetchone()[0]
    c.close()
    return primary, collateral, events, integrity


def init_db(db: Path) -> None:
    c = sqlite3.connect(db)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=FULL')
    c.execute('CREATE TABLE state(id INTEGER PRIMARY KEY CHECK(id=1), primary_value TEXT NOT NULL, collateral_value TEXT NOT NULL)')
    c.execute('INSERT INTO state VALUES(1,?,?)', (INITIAL_PRIMARY, INITIAL_COLLATERAL))
    c.execute('CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, primary_value TEXT NOT NULL, collateral_value TEXT NOT NULL, ns INTEGER NOT NULL)')
    c.commit()
    c.close()


def one(case: dict, out: Path):
    out.mkdir(parents=True, exist_ok=False)
    db = out / 'effect.sqlite'
    init_db(db)
    started_ns = time.perf_counter_ns()
    scenario = case['scenario']

    if scenario == 'correct':
        effect_primary, effect_collateral = INTENDED_PRIMARY, INITIAL_COLLATERAL
    else:
        effect_primary, effect_collateral = 'wrong', INITIAL_COLLATERAL

    effect_receipt = run_receiver(db, 'effect', effect_primary, effect_collateral)
    after_primary, after_collateral, events_after_effect, integrity_after_effect = read_db(db)
    verified_after_effect = (
        after_primary == INTENDED_PRIMARY and after_collateral == INITIAL_COLLATERAL
    )

    compensation_receipt = None
    if not verified_after_effect:
        if scenario == 'wrong_compensated_clean':
            compensation_receipt = run_receiver(
                db, 'compensation', INITIAL_PRIMARY, INITIAL_COLLATERAL
            )
        elif scenario == 'wrong_compensated_collateral':
            compensation_receipt = run_receiver(
                db, 'compensation', INITIAL_PRIMARY, 'damaged'
            )
        elif scenario == 'wrong_uncompensated':
            compensation_receipt = {
                'returncode': 98,
                'stdout': '',
                'stderr': 'compensation deliberately unavailable',
            }
        else:
            raise ValueError(scenario)

    final_primary, final_collateral, events, integrity_final = read_db(db)
    primary_restored = final_primary == INITIAL_PRIMARY
    collateral_preserved = final_collateral == INITIAL_COLLATERAL
    full_restoration = primary_restored and collateral_preserved

    if verified_after_effect:
        outcome = 'EFFECT_VERIFIED'
    elif full_restoration and any(e['kind'] == 'compensation' for e in events):
        outcome = 'EFFECT_CONTRADICTED_COMPENSATED'
    elif primary_restored and any(e['kind'] == 'compensation' for e in events):
        outcome = 'EFFECT_CONTRADICTED_COMPENSATION_PARTIAL'
    else:
        outcome = 'EFFECT_CONTRADICTED_UNCOMPENSATED'

    # Deliberately weak control: "compensated" is inferred from primary restoration alone.
    if verified_after_effect:
        primary_only = 'VERIFIED'
    elif primary_restored:
        primary_only = 'COMPENSATED'
    else:
        primary_only = 'CONTRADICTED'

    finished_ns = time.perf_counter_ns()
    row = {
        **case,
        'initial_primary': INITIAL_PRIMARY,
        'initial_collateral': INITIAL_COLLATERAL,
        'intended_primary': INTENDED_PRIMARY,
        'after_effect_primary': after_primary,
        'after_effect_collateral': after_collateral,
        'verified_after_effect': verified_after_effect,
        'final_primary': final_primary,
        'final_collateral': final_collateral,
        'primary_restored': primary_restored,
        'collateral_preserved': collateral_preserved,
        'full_restoration': full_restoration,
        'events_after_effect': events_after_effect,
        'events': events,
        'integrity_after_effect': integrity_after_effect,
        'integrity_final': integrity_final,
        'effect_receipt': effect_receipt,
        'compensation_receipt': compensation_receipt,
        'outcome': outcome,
        'primary_only_outcome': primary_only,
        'started_ns': started_ns,
        'finished_ns': finished_ns,
    }
    dump(out / 'result.json', row)
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('plan', type=Path)
    ap.add_argument('out', type=Path)
    a = ap.parse_args()
    plan = json.loads(a.plan.read_text())
    a.out.mkdir(parents=True, exist_ok=True)
    rows = [one(case, a.out / case['id']) for case in plan['cases']]
    dump(a.out / 'rows.json', rows)


if __name__ == '__main__':
    main()
