"""Read-only auditor: stdlib SHA1/zlib Git objects, no Git process or producer imports."""
from __future__ import annotations
import argparse, hashlib, json, re, zlib
from pathlib import Path

WRITE = 'output/effect.txt'
GOOD = {'correct', 'unrelated_preserved'}
WRONG_EFFECT = {'wrong_bytes', 'wrong_mode', 'wrong_kind', 'target_deleted'}
COMMON_REASONS = {'extra_change': 'scope_mismatch', 'no_op': 'scope_mismatch',
                  'wrong_parent': 'parent_mismatch', 'read_conflict': 'read_conflict',
                  'write_conflict': 'write_conflict', 'ref_race': 'cas_rejected'}


def require(ok, message):
    if not ok: raise AssertionError(message)


def load(path): return json.loads(Path(path).read_text())


def blob_id(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


class Objects:
    def __init__(self, repo): self.repo = Path(repo); self.cache = {}

    def get(self, oid):
        require(type(oid) is str and re.fullmatch('[0-9a-f]{40}', oid), 'invalid OID')
        if oid not in self.cache:
            compressed = (self.repo / 'objects' / oid[:2] / oid[2:]).read_bytes()
            decoder = zlib.decompressobj(); raw = decoder.decompress(compressed) + decoder.flush()
            require(decoder.eof and not decoder.unused_data, 'bad zlib object')
            require(hashlib.sha1(raw).hexdigest() == oid, 'object hash mismatch')
            head, body = raw.split(b'\0', 1); kind, length = head.split(b' ', 1)
            require(int(length) == len(body), 'object length mismatch')
            self.cache[oid] = kind.decode(), body
        return self.cache[oid]

    def files(self, tree, prefix=''):
        kind, data = self.get(tree); require(kind == 'tree', 'expected tree')
        result = {}; pos = 0; names = set()
        while pos < len(data):
            stop = data.index(b'\0', pos); mode, name = data[pos:stop].split(b' ', 1)
            oid = data[stop+1:stop+21].hex(); pos = stop+21
            require(len(oid) == 40 and name not in names and name not in (b'.', b'..'), 'tree entry invalid')
            require(b'/' not in name and name, 'tree name invalid'); names.add(name)
            key = prefix + name.decode(); mode = mode.decode()
            if mode in ('40000', '040000'):
                result.update(self.files(oid, key + '/'))
            else:
                actual_kind, body = self.get(oid)
                require(actual_kind == 'blob', 'fixture requires blob entries')
                require(mode in ('100644', '100755', '120000'), 'unexpected fixture mode')
                result[key] = {'mode': mode, 'kind': actual_kind, 'oid': oid, 'hex': body.hex()}
        require(pos == len(data), 'tree ended mid-entry')
        return result

    def commit(self, oid):
        kind, raw = self.get(oid); require(kind == 'commit', 'expected commit')
        lines = raw.split(b'\n\n', 1)[0].splitlines()
        trees = [v[5:].decode() for v in lines if v.startswith(b'tree ')]
        parents = [v[7:].decode() for v in lines if v.startswith(b'parent ')]
        require(len(trees) == 1, 'commit tree multiplicity')
        return self.files(trees[0]), parents


def entry(value):
    return None if value is None else [value['mode'], value['kind'], value['oid']]


def audit_case(directory, expected):
    d = Path(directory); row = load(d / 'result.json'); request = load(d / 'request.json')
    for k in ('id', 'rep', 'scenario', 'policy'): require(row[k] == expected[k], 'case identity')
    clocks = [row[k] for k in ('planned_ns', 'validated_ns', 'publish_start_ns', 'publish_end_ns')]
    require(all(type(v) is int and v >= 0 for v in clocks), 'clock type')
    require(clocks == sorted(clocks), 'clock order')
    o = Objects(d / 'repo.git'); scenario = row['scenario']; policy = row['policy']
    a, ap = o.commit(row['plan_oid']); before, bp = o.commit(row['current'])
    proposed, pp = o.commit(row['candidate']); precommit, _ = o.commit(row['precommit'])
    final_oid = (d / 'repo.git/refs/heads/target').read_text().strip()
    require(final_oid == row['final'], 'final ref mismatch'); final, fp = o.commit(final_oid)
    token = f"r{row['rep']:02d}-{scenario}"; desired = ('desired-' + token + '\n').encode()
    original = {'declared.txt': ('100644', b'allow\n'), 'hidden.txt': ('100644', b'allow\n'),
                WRITE: ('100644', ('old-' + token + '\n').encode()),
                'keep/unrelated.txt': ('100644', ('keep-' + token + '\n').encode()),
                'keep/mode.txt': ('100755', b'unchanged executable mode\n')}
    require(set(a) == set(original) and not ap, 'initial fixture structure')
    for name, (mode, data) in original.items():
        require(a[name]['hex'] == data.hex() and a[name]['mode'] == mode, 'initial fixture bytes')
    expected_before = {k: dict(v) for k, v in a.items()}
    mutation = {'unrelated_preserved': ('keep/unrelated.txt', b'new unrelated\n'),
                'read_conflict': ('hidden.txt', b'deny\n'),
                'write_conflict': (WRITE, b'new competing edit\n')}.get(scenario)
    if mutation:
        path, data = mutation
        expected_before[path] = dict(mode='100644', kind='blob', oid=blob_id(data), hex=data.hex())
        require(bp == [row['plan_oid']], 'precheck ancestry')
    else: require(row['current'] == row['plan_oid'], 'unexpected precheck change')
    require(before == expected_before, 'precheck fixture mismatch')
    require(request['plan_oid'] == row['plan_oid'] and request['expected_bytes_hex'] == desired.hex(), 'request identity/content')
    require(request['reads'] == {p: entry(a[p]) for p in ('declared.txt','hidden.txt')}, 'read request')
    require(request['before'] == {WRITE: entry(a[WRITE])}, 'write precondition')
    require(request['after'] == {WRITE: ['100644','blob',blob_id(desired)]}, 'after-state request')
    changes = sorted(k for k in set(before) | set(proposed) if before.get(k) != proposed.get(k))
    read_ok = all(before[k] == a[k] for k in ('declared.txt','hidden.txt'))
    write_ok = before[WRITE] == a[WRITE]
    scope_ok = changes == [WRITE]; parent_ok = pp == [row['current']]
    target_ok = proposed.get(WRITE) == dict(mode='100644',kind='blob',oid=blob_id(desired),hex=desired.hex())
    checks = dict(read_ok=read_ok, write_ok=write_ok, scope_ok=scope_ok,
                  parent_ok=parent_ok, post_ok=target_ok, changed_paths=changes)
    for key, value in checks.items():
        require(type(row['receipt'][key]) is type(value) and row['receipt'][key] == value, 'guard receipt: '+key)
    guard_reason = next((reason for ok, reason in ((read_ok,'read_conflict'),
        (write_ok,'write_conflict'),(scope_ok,'scope_mismatch'),(parent_ok,'parent_mismatch'),
        (target_ok or policy=='scope_only','postcondition_mismatch')) if not ok), 'eligible')
    require(row['receipt']['reason'] == guard_reason, 'guard reason')
    actual_reason = 'applied' if scenario in GOOD else COMMON_REASONS.get(scenario)
    if scenario in WRONG_EFFECT: actual_reason = 'applied' if policy=='scope_only' else 'postcondition_mismatch'
    require(row['reason'] == actual_reason, 'unexpected policy outcome')
    if scenario == 'ref_race':
        expected_raced = dict(before); data = b'after validation\n'
        expected_raced['keep/unrelated.txt'] = dict(mode='100644',kind='blob',oid=blob_id(data),hex=data.hex())
        require(precommit == expected_raced, 'missing race actor')
    else: require(row['precommit'] == row['current'], 'unexpected race')
    applied = row['reason']=='applied'; attempted = guard_reason=='eligible'
    if applied: require(type(row['returncode']) is int and row['returncode']==0 and final_oid==row['candidate'], 'publish return')
    elif attempted: require(type(row['returncode']) is int and row['returncode']!=0 and final_oid==row['precommit'], 'CAS return')
    else: require(row['returncode'] is None and final_oid==row['precommit'], 'refusal mutated target')
    if not attempted: require(row['stderr']=='', 'unexpected refusal stderr')
    if row['reason']=='cas_rejected':
        require(row['current'] in row['stderr'] and row['precommit'] in row['stderr'], 'CAS mismatch evidence')
    commands = [json.loads(v) for v in (d/'commands.jsonl').read_text().splitlines()]
    last = -1; publications = []
    for c in commands:
        require(type(c['start_ns']) is int and type(c['end_ns']) is int, 'native clock type')
        require(last <= c['start_ns'] <= c['end_ns'], 'native clock order'); last=c['end_ns']
        if 'publish candidate' in c['argv']: publications.append(c)
        elif c['rc'] != 0: raise AssertionError('unexpected native command error')
    require(len(publications) == int(attempted), 'publication attempt count')
    if attempted:
        c=publications[0]
        require(c['argv']==['update-ref','-m','publish candidate','refs/heads/target',row['candidate'],row['current']], 'unbound publication')
        require(c['rc']==row['returncode'] and c['stderr']==row['stderr'], 'native return receipt')
        require(row['publish_start_ns'] <= c['start_ns'] <= c['end_ns'] <= row['publish_end_ns'], 'publication bracket')
    logs = (d/'repo.git/logs/refs/heads/target').read_text().splitlines()
    transitions = [(v.split()[0],v.split()[1],v.split('\t',1)[1]) for v in logs]
    expected_log=[('0'*40,row['plan_oid'],'baseline')]
    if mutation: expected_log.append((row['plan_oid'],row['current'],'precheck change'))
    if scenario=='ref_race': expected_log.append((row['current'],row['precommit'],'postcheck actor'))
    if applied: expected_log.append((row['current'],row['candidate'],'publish candidate'))
    require(transitions==expected_log, 'reflog')
    outside = {k:v for k,v in final.items() if k!=WRITE} == {k:v for k,v in before.items() if k!=WRITE}
    effect_met = final.get(WRITE)==dict(mode='100644',kind='blob',oid=blob_id(desired),hex=desired.hex())
    should_apply = scenario in GOOD
    task_correct = (applied and effect_met and outside and fp==[row['current']]) if should_apply else (not applied and final_oid==row['precommit'])
    # Validate every retained loose object including rejected candidates, without Git.
    for p in (d/'repo.git/objects').glob('??/*'):
        if p.is_file(): o.get(p.parent.name + p.name)
    return dict(id=row['id'],rep=row['rep'],policy=policy,scenario=scenario,
                applied=applied,reason=row['reason'],task_correct=task_correct,
                effect_met=effect_met,wrong_publication=applied and not should_apply,
                preserved_on_refusal=(not applied and final_oid==row['precommit']),
                plan_oid=row['plan_oid'],current=row['current'],candidate=row['candidate'],
                native_commands=len(commands),verified_objects=len(o.cache))


def audit_all(root, plan):
    root=Path(root); cases=plan['cases']; ids=[c['id'] for c in cases]
    require(len(ids)==len(set(ids)), 'duplicate planned IDs')
    require(load(root/'completed.json')['count']==len(cases), 'incomplete allocation')
    require(load(root/'started.json')['allocation']==plan['allocation'], 'allocation identity')
    present={p.name for p in root.iterdir() if p.is_dir()}
    require(present==set(ids), 'missing or unexpected cases')
    rows=[audit_case(root/c['id'],c) for c in cases]; pairs={}; summary={}
    for r in rows:
        key=(r['rep'],r['scenario']); signature=(r['plan_oid'],r['current'],r['candidate'])
        if key in pairs: require(pairs[key]==signature, 'paired inputs differ')
        pairs[key]=signature
        s=summary.setdefault(r['policy'],dict(cases=0,correct=0,applied=0,wrong_publications=0,refused=0))
        s['cases']+=1; s['correct']+=int(r['task_correct']); s['applied']+=int(r['applied'])
        s['wrong_publications']+=int(r['wrong_publication']); s['refused']+=int(not r['applied'])
    return dict(schema='candidate-postcondition-audit-v1',integrity_cases=len(rows),
                paired_cases=len(pairs),summary=summary,rows=rows)


def main():
    p=argparse.ArgumentParser(); p.add_argument('plan',type=Path);p.add_argument('root',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args(); result=audit_all(a.root,load(a.plan));a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))

if __name__=='__main__': main()
