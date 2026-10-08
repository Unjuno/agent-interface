from __future__ import annotations
import argparse,copy,json,shutil,tempfile
from pathlib import Path
import audit

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); a=ap.parse_args(); src=Path(a.root); rows=[json.loads(x) for x in (src/'ledger.jsonl').read_text().splitlines() if x]
    assert not audit.audit(src,src/'ledger.jsonl')['failed']; print('PASS clean')
    def mut(name,fn):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'r'; shutil.copytree(src,root); rs=copy.deepcopy(rows); fn(rs,root); led=root/'m.jsonl'; led.write_text(''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rs)); out=audit.audit(root,led); assert out['failed'],name; print('REJECT',name,out['failed'][0]['errors'])
    def loser(rs):
        return 'b' if rs[0]['workers']['a']['result']['receipt']['outcome']=='APPLIED' else 'a'
    mut('two_applied',lambda rs,root: rs[0]['workers'][loser(rs)]['result']['receipt'].__setitem__('outcome','APPLIED'))
    mut('second_effect',lambda rs,root: rs[0]['workers'][loser(rs)]['result'].__setitem__('new_effects',1))
    mut('conflict_reason',lambda rs,root: rs[0]['workers'][loser(rs)]['result']['receipt'].__setitem__('reason','valid'))
    mut('db_delta',lambda rs,root: rs[0]['db']['effects'][0].__setitem__('delta',9))
    mut('hide_overlap',lambda rs,root: rs[0]['workers']['b'].__setitem__('call_enter_ns',10**30))
    mut('replay_new_effect',lambda rs,root: rs[0]['replays']['a'].__setitem__('stdout',rs[0]['replays']['a']['stdout'].replace('"new_effects":0','"new_effects":1')))
    mut('event_pid',lambda rs,root:(root/rs[0]['case_id']/'a.events.jsonl').write_text((root/rs[0]['case_id']/'a.events.jsonl').read_text().replace(f'"pid":{rs[0]["workers"]["a"]["pid"]}','"pid":999999')))
    print('PASS mutation controls')
if __name__=='__main__': main()
