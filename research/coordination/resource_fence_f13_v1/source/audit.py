"""Independent table oracle and read-only reconstruction of retained DB/IPC."""
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

MODES = ('ISSUER_ONLY', 'MAX_SEEN', 'INSTALLED_EPOCH')
SCENARIOS = ('STABLE', 'IDLE_RETIRE', 'NEW_FIRST', 'DELAYED_FENCE', 'PREINSTALL_NEW', 'RESOURCE_RESTART')
# An explicit directed oracle, not an import of the actor's predicate.
OUTCOMES = {
 'STABLE': [('APPLIED',), ('APPLIED',), ('APPLIED',)],
 'IDLE_RETIRE': [('APPLIED',), ('APPLIED',), ('WRONG_EPOCH',)],
 'NEW_FIRST': [('APPLIED','APPLIED'), ('APPLIED','OLD_TOKEN'), ('APPLIED','WRONG_EPOCH')],
 'DELAYED_FENCE': [('APPLIED','APPLIED','APPLIED'), ('APPLIED','APPLIED','APPLIED'), ('APPLIED','WRONG_EPOCH','APPLIED')],
 'PREINSTALL_NEW': [('APPLIED','APPLIED','APPLIED'), ('APPLIED','APPLIED','OLD_TOKEN'), ('WRONG_EPOCH','APPLIED','WRONG_EPOCH')],
 'RESOURCE_RESTART': [('APPLIED','APPLIED'), ('APPLIED','APPLIED'), ('WRONG_EPOCH','APPLIED')]
}
ORDER = {'STABLE':['old-A'], 'IDLE_RETIRE':['old-A'], 'NEW_FIRST':['new-A','old-A'],
         'DELAYED_FENCE':['old-A','old-B','new-A'], 'PREINSTALL_NEW':['new-A','new-B','old-A'],
         'RESOURCE_RESTART':['old-A','new-A']}


def decoded_db(encoded):
    raw = base64.b64decode(encoded, validate=True)
    with tempfile.TemporaryDirectory() as temp:
        p = Path(temp) / 'copy.db'
        p.write_bytes(raw)
        with sqlite3.connect(p.as_uri() + '?mode=ro', uri=True) as db:
            if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise ValueError('DB integrity')
            m = dict(db.execute('SELECT k,v FROM meta'))
            s = {'scope':m['scope'], 'epoch':int(m['epoch']), 'highwater':int(m['highwater']),
                 'entries':[list(x) for x in db.execute('SELECT * FROM entries ORDER BY id')]}
            j = [(json.loads(a), json.loads(b)) for a,b in db.execute('SELECT request,response FROM journal ORDER BY n')]
            return s, j


def audit(root, records_path):
    root, records_path = Path(root), Path(records_path)
    obj = json.loads(records_path.read_text())
    errors, checks = [], 0
    def check(ok, msg):
        nonlocal checks
        checks += 1
        if not ok: errors.append(msg)
    rows = obj['cases']
    expected = [(s,m,k) for s in SCENARIOS for m in MODES for k in range(2)]
    check([(r['scenario'],r['mode'],r['rep']) for r in rows] == expected, 'coverage/order')
    check(obj['phase'] == 'formal', 'phase')
    freeze = json.loads((root/'source/FREEZE.json').read_text())
    for name, digest in freeze['sha256'].items():
        check(hashlib.sha256((root/'source'/name).read_bytes()).hexdigest() == digest, 'source:'+name)
    totals = {m:{'cases':0,'applied':0,'old_after_issuer_retire':0,'old_after_resource_install':0,
                 'new_applied':0,'new_refused':0,'installation_commands':0,'effect_requests':0} for m in MODES}
    exits = {}
    for row in rows:
        tag, mode, scenario = row['id'], row['mode'], row['scenario']
        t = totals[mode]; t['cases'] += 1
        current = {role:decoded_db(row['initial_db'][role+'.db'])[0] for role in ('issuer','resource')}
        for role in current:
            check(current[role] == {'scope':tag,'epoch':7,'highwater':7,'entries':[]}, tag+':initial:'+role)
        peers = {p['name']:p for p in row['peers']}
        expected_peers = ['issuer0','resource0'] + (['resource1'] if scenario=='RESOURCE_RESTART' else [])
        check(list(peers)==expected_peers, tag+':peer coverage')
        check(len({p['pid'] for p in peers.values()})==len(peers), tag+':distinct pids')
        for p in peers.values():
            boot = json.loads(p['boot_raw'])
            check(p['pid']>0 and boot['pid']==p['pid'] and boot['role']==p['role'] and boot['mode']==mode, tag+':boot identity')
            ex = 23 if scenario=='RESOURCE_RESTART' and p['name']=='resource0' else 0
            check(p['exit']==ex and p['stderr']=='',tag+':process exit')
            check('BEGIN IMMEDIATE' in p['sql'] and 'COMMIT' in p['sql'],tag+':SQL trace')
            check('-S' in p['argv'] and '-B' in p['argv'], tag+':startup')
            exits[str(p['exit'])] = exits.get(str(p['exit']),0)+1
        journal = {'issuer':[], 'resource':[]}
        grants, apply_ids, statuses = {}, [], []
        previous_end = 0
        seen_boot = set()
        for event in row['io']:
            p = peers[event['peer']]; role = p['role']
            check(event['end_ns'] >= event['start_ns'] >= previous_end, tag+':IPC ordering')
            previous_end = event['end_ns']
            check(event['request_raw'].endswith('\n') and event['response_raw'].endswith('\n'),tag+':wire framing')
            q, a = json.loads(event['request_raw']), json.loads(event['response_raw'])
            if p['name'] not in seen_boot:
                check(json.loads(p['boot_raw'])['state']==current[role],tag+':boot state')
                seen_boot.add(p['name'])
            if q['op'] in ('close','exit23'):
                check(a['status']==('CLOSED' if q['op']=='close' else 'EXIT23'),tag+':termination marker')
                if q['op']=='exit23':
                    for rr in current:
                        check(decoded_db(row['restart_db'][rr+'.db'])[0]==current[rr],tag+':restart snapshot')
                continue
            before = json.loads(json.dumps(current[role]))
            check(a['before']==before,tag+':before state')
            check(a['authority_granted'] is False and a['task_success'] is None,tag+':authority/effect distinction')
            if role=='issuer' and q['op']=='grant':
                check(q['value']==({'old-A':11,'old-B':12,'new-A':21,'new-B':21}.get(q['id'])),tag+':declared value')
                g={'scope':tag,'id':q['id'],'epoch':before['epoch'],'value':q['value']}
                check(a['status']=='GRANTED' and a['grant']==g,tag+':grant')
                grants[g['id']]=g
                current[role]['entries'].append([g['id'],g['epoch'],g['value']])
            elif role=='issuer' and q['op']=='retire':
                check(q=={'op':'retire','expected':7,'next':8} and a['status']=='RETIRED',tag+':issuer retirement')
                current[role]['epoch']=8
            elif role=='resource' and q['op']=='install':
                check(mode=='INSTALLED_EPOCH' and q=={'op':'install','expected':7,'next':8} and a['status']=='INSTALLED',tag+':resource installation')
                current[role]['epoch']=8; t['installation_commands']+=1
            elif role=='resource' and q['op']=='apply':
                g=q['grant']; apply_ids.append(g['id']); statuses.append(a['status']); t['effect_requests']+=1
                check(g==grants.get(g['id']),tag+':issued content binding')
                if a['status']=='APPLIED':
                    current[role]['entries'].append([g['id'],g['epoch'],g['value']])
                    current[role]['highwater']=max(before['highwater'],g['epoch'])
                    t['applied']+=1
                    if g['epoch']==7 and current['issuer']['epoch']==8: t['old_after_issuer_retire']+=1
                    if g['epoch']<before['epoch']: t['old_after_resource_install']+=1
                    if g['epoch']==8: t['new_applied']+=1
                elif g['epoch']==8: t['new_refused']+=1
            else:
                check(False,tag+':unexpected command')
            current[role]['entries'].sort()
            check(a['after']==current[role],tag+':after state')
            journal[role].append((q,a))
        check(apply_ids==ORDER[scenario],tag+':effect request order')
        check(tuple(statuses)==OUTCOMES[scenario][MODES.index(mode)],tag+':directed decision oracle')
        for role in current:
            final, logged = decoded_db(row['final_db'][role+'.db'])
            check(final==current[role],tag+':final database')
            check(logged==journal[role],tag+':database journal/IPC')
        check(t['old_after_resource_install']==0, tag+':post-install exclusion')
    for i, receipt in enumerate(obj['batches']):
        check(receipt['batch']==i and receipt['returncode']==0 and receipt['pid']>0 and not receipt['timeout'], 'batch process')
    check(len(obj['batches'])==6,'six batches')
    check(totals['INSTALLED_EPOCH']['old_after_issuer_retire']==2,'pre-fence limitation retained')
    check(totals['INSTALLED_EPOCH']['new_refused']==2,'premature-new limitation retained')
    check(sum(t['effect_requests'] for t in totals.values())==72,'72 effect requests')
    return {'decision':'PASS_RESOURCE_FENCE_BOUNDARY_SCOPED' if not errors else 'FAIL_OR_HOLD_RESOURCE_FENCE',
            'checks':checks,'errors':errors,'cases':len(rows),'totals':totals,'actor_exits':exits,
            'records_sha256':hashlib.sha256(records_path.read_bytes()).hexdigest()}


if __name__=='__main__':
    result=audit(sys.argv[1],sys.argv[2])
    print(json.dumps(result,sort_keys=True,indent=2))
    raise SystemExit(bool(result['errors']))
