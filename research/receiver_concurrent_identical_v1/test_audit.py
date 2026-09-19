from __future__ import annotations
import argparse, copy, json, shutil, tempfile
from pathlib import Path
import audit

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); a=ap.parse_args(); src=Path(a.root)
    rows=[json.loads(x) for x in (src/'ledger.jsonl').read_text().splitlines() if x.strip()]
    clean=audit.audit(src,src/'ledger.jsonl'); assert not clean['failed']; print('PASS clean')
    def run_mut(name, mut):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'r'; shutil.copytree(src,root)
            rs=copy.deepcopy(rows); mut(rs,root)
            led=root/'mut.jsonl'; led.write_text(''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rs))
            out=audit.audit(root,led)
            if not out['failed']: raise AssertionError(f'{name}: mutation accepted')
            print('REJECT',name,out['failed'][0]['errors'])
    run_mut('duplicate_effect_count', lambda rs,root: rs[0]['workers']['a']['result'].__setitem__('new_effects',1))
    run_mut('receipt_mismatch', lambda rs,root: rs[0]['workers']['a']['result']['receipt'].__setitem__('reason','corrupt'))
    run_mut('hide_overlap', lambda rs,root: rs[0]['workers']['b'].__setitem__('call_enter_ns',10**30))
    run_mut('replay_new_effect', lambda rs,root: rs[0]['replay'].__setitem__('stdout',rs[0]['replay']['stdout'].replace('"new_effects":0','"new_effects":1')))
    run_mut('db_snapshot_fabrication', lambda rs,root: rs[0]['db']['effects'][0].__setitem__('delta',7))
    run_mut('wrong_db_hash', lambda rs,root: rs[0].__setitem__('db_sha256','00'*32))
    run_mut('event_pid', lambda rs,root: (root/rs[0]['case_id']/'a.events.jsonl').write_text((root/rs[0]['case_id']/'a.events.jsonl').read_text().replace(f'"pid":{rs[0]["workers"]["a"]["pid"]}', '"pid":999999'),encoding='utf-8'))
    print('PASS mutation controls')
if __name__=='__main__': main()
