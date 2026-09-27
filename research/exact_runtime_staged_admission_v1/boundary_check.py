#!/usr/bin/env python3
"""Six two-connection schedule checks through the unchanged runtime/adapters."""
from __future__ import annotations
import argparse, copy, hashlib, json, sqlite3, tempfile
from pathlib import Path
from runner import Adapter, encode, initial, interface, load_runtime

class BoundaryAdapter(Adapter):
    def store(self, state):
        super().store(state)
        if getattr(self, 'inject_before_validation', False):
            self.inject_before_validation = False
            self.write_competitor('writer_before_validation')

    def write_competitor(self, label):
        self.writer.execute('BEGIN IMMEDIATE')
        before = {k: json.loads(v) for k,v in self.writer.execute('SELECT k,v FROM state')}
        self.writer.execute('UPDATE state SET v=? WHERE k=?', (encode(-self.case['source']['x']), 'x'))
        self.writer.execute('UPDATE state SET v=? WHERE k=?', (encode(before['version']+1), 'version'))
        self.writer.execute('COMMIT')
        self.schedule.append(dict(event=label, before=before))

    def admit(self, request):
        self.inject_before_validation = self.order == 'writer_first'
        result = super().admit(request)
        self.schedule.append(dict(event='admission_return', eligible=result['eligible'], transaction_open=self.db.in_transaction))
        if self.order == 'checker_first':
            assert result['eligible'] and self.db.in_transaction
            try:
                self.writer.execute('BEGIN IMMEDIATE')
            except sqlite3.OperationalError as exc:
                self.schedule.append(dict(event='writer_blocked', code=exc.sqlite_errorcode, name=exc.sqlite_errorname))
                assert exc.sqlite_errorcode == sqlite3.SQLITE_BUSY
            else:
                self.writer.rollback()
                raise AssertionError('competing connection unexpectedly acquired write transaction')
        return result

    def execute(self, request):
        result = super().execute(request)
        self.schedule.append(dict(event='effect_committed', transaction_open=self.db.in_transaction))
        if self.order == 'checker_first': self.write_competitor('writer_after_effect')
        return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    runtime=load_runtime(Path(__file__).parent/'vendor/compiled_gui_interface_v1.py')
    rows=[]
    with (a.out/'raw.jsonl').open('x') as out:
        for direction in (-1,1):
            for order in ('stable','writer_first','checker_first'):
                with tempfile.TemporaryDirectory(prefix='er197-') as temp:
                    source=initial(direction)
                    case=dict(suite='boundary',kind='cert',name=order,source=source,current=dict(source,version=1))
                    adapter=BoundaryAdapter(interface('cert'),case,'certified')
                    target=sqlite3.connect(str(Path(temp)/'state.db'),isolation_level=None,timeout=0)
                    adapter.db.backup(target);adapter.db.close();adapter.db=target
                    assert target.execute('PRAGMA journal_mode=WAL').fetchone()[0]=='wal'
                    adapter.writer=sqlite3.connect(str(Path(temp)/'state.db'),isolation_level=None,timeout=0)
                    adapter.order=order;adapter.schedule=[]
                    try:
                        row=adapter.run(runtime)
                        row['schedule']=adapter.schedule
                        row['final_world']={k:json.loads(v) for k,v in adapter.writer.execute('SELECT k,v FROM state')}
                        rows.append(row);out.write(encode(row)+'\n');out.flush()
                    finally:adapter.writer.close()
    # Independent checks use effects/pre-world rather than controller's eligibility calculation.
    for row in rows:
        order=row['case']['name'];source=row['case']['source'];receipt=row['receipt']
        names=[x['event'] for x in row['schedule']]
        if order=='writer_first':
            assert row['execute_calls']==0 and not row['effects']
            assert receipt['outcome']=='SAFE_YIELD'
            assert names==['writer_before_validation','admission_return']
        else:
            assert row['execute_calls']==1 and len(row['effects'])==1
            assert row['effects'][0]['pre_world']['x']==source['x']
            assert receipt['outcome']=='TASK_SUCCEEDED'
            if order=='checker_first':
                assert names==['admission_return','writer_blocked','effect_committed','writer_after_effect']
                assert row['schedule'][1]['code']==sqlite3.SQLITE_BUSY
                assert row['final_world']['x']==-source['x']
                assert row['schedule'][-1]['before']['done'] is True
        assert not row['transaction_left_open']
    result=dict(status='PASS_TWO_CONNECTION_ORDERINGS',runtime_invocations=6,
                stable_success=2,writer_first_rejected=2,checker_first_busy_then_effect_then_writer=2,
                raw_sha256=hashlib.sha256((a.out/'raw.jsonl').read_bytes()).hexdigest(),
                scope='deterministic two-connection interleavings, not a scheduling-frequency or physical-input benchmark')
    (a.out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
