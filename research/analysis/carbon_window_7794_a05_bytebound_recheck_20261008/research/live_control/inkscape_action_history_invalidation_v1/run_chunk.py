#!/usr/bin/env python3
import argparse, json, subprocess, sys
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--schedule', required=True)
p.add_argument('--out', required=True)
p.add_argument('--chunk', type=int, choices=[1,2,3,4], required=True)
p.add_argument('--display-base', type=int, default=840)
a=p.parse_args()
schedule=json.load(open(a.schedule))
rows=[r for r in schedule['cases'] if r['chunk']==a.chunk]
if len(rows)!=4:
    raise RuntimeError(f'expected four rows for chunk {a.chunk}, got {len(rows)}')
out=Path(a.out); out.mkdir(parents=True, exist_ok=True)
ledger_path=out/f'ledger_chunk_{a.chunk}.json'
if ledger_path.exists():
    raise RuntimeError(f'refuse rerun existing chunk ledger {ledger_path}')
ledger=[]
for j,row in enumerate(rows):
    case_out=out/row['case_id']
    if case_out.exists():
        raise RuntimeError(f"refuse rerun existing case path {row['case_id']}")
    display_num=a.display_base+(a.chunk-1)*10+j
    cp=subprocess.run([
        sys.executable, str(Path(__file__).with_name('run_case.py')),
        '--out', str(case_out), '--context', row['context'], '--policy', row['policy'],
        '--display', str(display_num),
    ], capture_output=True, text=True)
    ledger.append({
        'case_id': row['case_id'], 'context': row['context'], 'policy': row['policy'],
        'display_num': display_num, 'returncode': cp.returncode,
        'stdout': cp.stdout, 'stderr': cp.stderr,
    })
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True)+'\n')
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)
print(json.dumps({'chunk': a.chunk, 'cases_completed': len(ledger), 'status': 'COMPLETE'}, sort_keys=True))
