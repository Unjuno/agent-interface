"""Independent raw/SQLite reconstruction. Does not import actor or runner."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

MODES = ('REVISION_ONLY', 'CURRENT_DDL', 'SCHEMA_COOKIE')
NAMES = ('STABLE', 'NORMAL_INSERT', 'OTHER_TENANT_INSERT', 'MISSING_AT_PREPARE',
         'DROP_THEN_INSERT', 'RESTORE_AFTER_INSERT', 'RESTORE_NO_DATA',
         'UNRELATED_DDL', 'ROLLED_BACK_MIGRATION')


def same(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def db_state(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        return {'identity': db.execute('SELECT identity FROM meta').fetchone()[0],
                'cookie': db.execute('PRAGMA main.schema_version').fetchone()[0],
                'scopes': db.execute('SELECT * FROM scopes ORDER BY tenant').fetchall(),
                'items': db.execute('SELECT * FROM items ORDER BY id').fetchall(),
                'effects': db.execute('SELECT * FROM effects ORDER BY request_id').fetchall(),
                'triggers': db.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger' AND tbl_name='items' ORDER BY name").fetchall()}
    finally:
        db.close()


def audit_document(doc, directory):
    errors = []
    checked = 0
    def ck(ok, message):
        nonlocal checked
        checked += 1
        if not ok:
            errors.append(message)
    batch, reps = doc.get('batch'), doc.get('repetitions')
    ck(type(batch) is int and 0 <= batch < 9, 'BATCH')
    ck(type(reps) is int and reps in (1, 2), 'REPETITIONS')
    if errors:
        return {'errors': errors, 'checks': checked, 'summary': {}}
    expected_order = [(r, m) for r in range(reps)
                      for m in (MODES if r % 2 == 0 else tuple(reversed(MODES)))]
    ck(len(doc.get('rows', [])) == len(expected_order), 'DENOMINATOR')
    summary = {m: dict(cases=0, stored=0, refused=0, stale_stores=0,
                      conservative_refusals=0, unsupported=0) for m in MODES}
    for position, (repeat, mode) in enumerate(expected_order):
        if position >= len(doc.get('rows', [])):
            break
        row = doc['rows'][position]
        ident = f't61c-{batch}-{repeat}-{MODES.index(mode)}'
        prefix = ident + ':'
        ck(row.get('id') == ident and row.get('mode') == mode and
           row.get('condition') == NAMES[batch], prefix + 'IDENTITY_ORDER')
        directory_case = directory / ident
        actual = {}
        try:
            for phase in ('initial', 'before_prepare', 'prepared', 'changed', 'final'):
                actual[phase] = db_state(directory_case / (phase + '.sqlite'))
                ck(same(row['observations'][phase], actual[phase]), prefix + phase + '_DB')
        except (KeyError, OSError, sqlite3.Error, TypeError) as exc:
            errors.append(prefix + 'DB_OR_SCHEMA:' + type(exc).__name__)
            continue
        initial, before, prepared, changed, final = [actual[x] for x in ('initial','before_prepare','prepared','changed','final')]
        for state in actual.values():
            ck(state['identity'] == ident, prefix + 'DB_ID')
            ck(type(state['cookie']) is int, prefix + 'COOKIE_TYPE')
            ck(all(type(v) is int for _, v in state['scopes']), prefix + 'EPOCH_TYPE')
        ck(same(before, prepared), prefix + 'READ_ONLY_PREPARATION')
        ck(initial['items'] == [] and initial['effects'] == [] and
           dict(initial['scopes']) == {'A':0, 'B':0}, prefix + 'INITIAL')
        inserts_a = batch in (1, 3, 4, 5)
        inserts_b = batch == 2
        expected_items = [[1, 'A', 1, 9, 1]] if inserts_a else ([[1, 'B', 1, 9, 1]] if inserts_b else [])
        ck(same(changed['items'], expected_items), prefix + 'WRITER_EFFECT')
        ck(dict(changed['scopes']) == {'A':int(batch==1), 'B':int(batch==2)}, prefix + 'REVISION_COVERAGE')
        delta = (1 if batch in (3,4,7) else 2 if batch in (5,6) else 0)
        ck(changed['cookie'] == initial['cookie'] + delta, prefix + 'DDL_GENERATION')
        expected_triggers = [x for x in initial['triggers'] if x[0] != 'item_insert'] if batch in (3,4) else initial['triggers']
        ck(same(changed['triggers'], expected_triggers), prefix + 'TRIGGER_RESTORATION')
        ck(changed['effects'] == [], prefix + 'NO_EARLY_EFFECT')
        def basis(state):
            return dict(identity=state['identity'], cookie=state['cookie'],
                        epoch=dict(state['scopes'])['A'], triggers=state['triggers'])
        original_rows = [[i, payload, rev] for i,t,a,payload,rev in prepared['items'] if t=='A' and a==1]
        current_rows = [[i, payload, rev] for i,t,a,payload,rev in final['items'] if t=='A' and a==1]
        p = row['preparation']; d = row['decision']
        supported = mode == 'REVISION_ONLY' or same(prepared['triggers'], initial['triggers'])
        ck(same(p.get('basis'), basis(prepared)) and same(p.get('rows'), original_rows), prefix + 'PREPARATION_BYTES')
        ck(p.get('status') == ('PREPARED' if supported else 'UNSUPPORTED'), prefix + 'PREPARE_GATE')
        reasons = []
        if not supported:
            reasons.append('NO_PREPARATION')
        else:
            if dict(prepared['scopes'])['A'] != dict(changed['scopes'])['A']:
                reasons.append('EPOCH_CHANGED')
            if mode != 'REVISION_ONLY' and not same(changed['triggers'], initial['triggers']):
                reasons.append('TRIGGER_CONTRACT_CHANGED')
            if mode == 'SCHEMA_COOKIE' and prepared['cookie'] != changed['cookie']:
                reasons.append('SCHEMA_CHANGED')
        stored = not reasons
        ck(d.get('status') == ('STORED' if stored else 'REFUSED') and same(d.get('reasons'), reasons), prefix + 'DECISION')
        ck(same(d.get('basis'), basis(changed)) and d.get('authority') is False, prefix + 'DECISION_BASIS')
        expected_effects = [[ident,'A',json.dumps(original_rows,separators=(',',':'))]] if stored else []
        ck(same(final['effects'], expected_effects), prefix + 'FINAL_EFFECT')
        for key in ('identity','cookie','items','scopes','triggers'):
            ck(same(final[key], changed[key]), prefix + 'UNCHANGED_' + key)
        for role in ('reader','writer'):
            process = row['processes'][role]
            ck(type(process['exit']) is int and process['exit']==0 and process['stderr']=='', prefix+role+'_EXIT')
            boot = json.loads(process['boot'])
            ck(type(process['pid']) is int and process['pid']>0 and boot['pid']==process['pid'] and
               boot['argv']==process['argv'][3:] and boot['boot']==role, prefix+role+'_BOOT')
            ck(Path(process['argv'][3]).name=='actor.py' and process['argv'][4]==role and
               Path(process['argv'][5]).parent.name==ident and process['argv'][6]==mode,
               prefix+role+'_COMMAND')
            operations = []
            for call in process['calls']:
                request = json.loads(call['request']); response = json.loads(call['response'])
                ck(same(request, response['request']), prefix+role+'_IPC')
                ck(type(call['before_ns']) is int and type(call['after_ns']) is int and
                   call['before_ns'] <= call['after_ns'], prefix+role+'_BRACKET')
                operations.append(request['op'])
                if request['op'] == 'prepare':
                    ck(same(response['value'],p),prefix+'PREPARE_REPLY')
                    ck(response['sql'][0]=='BEGIN' and response['sql'][-1]=='COMMIT',prefix+'PREPARE_TXN')
                elif request['op'] == 'commit':
                    ck(same(response['value'],d),prefix+'COMMIT_REPLY')
                    ck(response['sql'][0]=='BEGIN IMMEDIATE' and response['sql'][-1]=='COMMIT',prefix+'COMMIT_TXN')
                    ck(not any('SELECT id,payload' in s for s in response['sql']),prefix+'NO_CURRENT_QUERY_ORACLE')
                elif request['op'] == 'change':
                    ck(response['sql'][0]=='BEGIN IMMEDIATE' and
                       response['sql'][-1]==('ROLLBACK' if request['rollback'] else 'COMMIT'),prefix+'WRITER_TXN')
            expected_ops = ['prepare','commit','stop'] if role=='reader' else (['change','change','stop'] if batch==3 else ['change','stop'])
            ck(operations==expected_ops,prefix+role+'_OP_ORDER')
        ck(row['processes']['reader']['pid'] != row['processes']['writer']['pid'],prefix+'SEPARATE_PROCESSES')
        s = summary[mode]; s['cases'] += 1; s['stored'] += int(stored); s['refused'] += int(not stored)
        s['stale_stores'] += int(stored and not same(original_rows,current_rows))
        s['conservative_refusals'] += int(supported and not stored and same(original_rows,current_rows))
        s['unsupported'] += int(not supported)
    return {'errors':errors,'checks':checked,'summary':summary}


def audit(root, freeze=None):
    paths = sorted(root.glob('batch-*/RAW.json'))
    errors = []; total_checks = 0; summaries = {}
    if len(paths) != 9:
        errors.append('BATCH_DENOMINATOR')
    for i,path in enumerate(paths):
        doc=json.loads(path.read_text()); r=audit_document(doc,path.parent)
        if doc.get('batch') != i or doc.get('repetitions') != 2:
            errors.append('FORMAL_SCHEDULE')
        receipt_path=path.parent/'EXECUTION.json'
        if not receipt_path.is_file():
            errors.append('MISSING_EXTERNAL_EXIT')
        else:
            receipt=json.loads(receipt_path.read_text())
            if type(receipt.get('exit')) is not int or receipt['exit']!=0 or receipt.get('raw_sha256')!=hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append('EXTERNAL_EXIT_OR_RAW')
        errors.extend(r['errors']); total_checks += r['checks']
        for mode,s in r['summary'].items():
            d=summaries.setdefault(mode,{k:0 for k in s})
            for k,v in s.items():d[k]+=v
    expected={'REVISION_ONLY':(6,0,0),'CURRENT_DDL':(2,0,2),'SCHEMA_COOKIE':(0,4,2)}
    for mode,counts in expected.items():
        s=summaries.get(mode,{})
        if s.get('cases')!=18 or tuple(s.get(k) for k in ('stale_stores','conservative_refusals','unsupported'))!=counts:
            errors.append('OUTCOME_GATE:'+mode)
    if freeze:
        f=json.loads(freeze.read_text())
        for rel,wanted in f['files'].items():
            if hashlib.sha256((freeze.parent/rel).read_bytes()).hexdigest()!=wanted:
                errors.append('SOURCE_CHANGED:'+rel)
    return {'decision':'PASS_TRIGGER_COVERAGE_LIFETIME_SCOPED' if not errors else 'HOLD_OR_FAIL',
            'checks':total_checks,'errors':errors,'summary':summaries}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--freeze',type=Path)
    p.add_argument('--out',type=Path);a=p.parse_args();result=audit(a.root,a.freeze)
    text=json.dumps(result,sort_keys=True,indent=2)+'\n'
    if a.out:
        with a.out.open('x') as f:f.write(text)
    print(text,end='');raise SystemExit(bool(result['errors']))
