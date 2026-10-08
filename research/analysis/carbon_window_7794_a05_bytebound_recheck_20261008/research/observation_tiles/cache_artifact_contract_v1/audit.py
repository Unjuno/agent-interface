"""Raw-only independent audit. Imports neither sink, candidate, trial nor Pillow."""
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from png_oracle import decode

POLICIES = ('ORIGINAL','BYTE_PIN_REPAIR','PIXEL_CHECK_REPAIR')
SCENARIOS = ('UNCHANGED','FRAME_CHANGED','CACHE_MISSING','CACHE_TRUNCATED',
 'CACHE_OTHER_PIXELS','CACHE_OTHER_GEOMETRY','CACHE_LOSSLESS_REENCODED','NEXT_NAME_OCCUPIED')
SENTINEL = b'occupied-evidence-do-not-overwrite\n'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate key')
        out[key] = value
    return out


def parse(s):
    return json.loads(s, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('constant')))


def unb(s):
    return base64.b64decode(s, validate=True)


def reference(rep, changed=False):
    out = bytearray()
    for y in range(64):
        for x in range(96):
            v = 19*rep + 5*y + 3*x + (71 if changed else 0)
            out.extend(((v+83*c) % 256 for c in (0,1,2)))
    return bytes(out)


def audit(root, source=None, construction=False, override=None, rep=None):
    source = source or Path(__file__).resolve().parent
    errors, checks, counts = [], 0, Counter()
    def need(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(label)
    try:
        raw_bytes = (root/'RAW.jsonl').read_bytes()
        rows = override if override is not None else [parse(s) for s in raw_bytes.splitlines()]
        reps = [100] if construction else [rep]
        schedule = [(r,s,p) for r in reps for s in SCENARIOS for p in POLICIES]
        need(len(rows)==len(schedule), 'row denominator')
        terminal = parse((root/'TERMINAL.json').read_text())
        execution = parse((root/'EXECUTION.json').read_text())
        need(type(execution['returncode']) is int and execution['returncode']==0, 'outer exit')
        need(execution['timeout'] is False and execution['stderr']=='', 'outer error')
        need(parse(execution['stdout'])==terminal, 'outer terminal bytes')
        need(terminal['status']=='COMPLETED' and terminal['error'] is None, 'terminal')
        need(type(terminal['rows']) is int and terminal['rows']==len(schedule), 'terminal count')
        need(type(terminal['planned']) is int and terminal['planned']==len(schedule), 'planned')
        if not construction:
            need(terminal['phase']=='batch'+str(rep) and terminal['construction'] is False, 'batch identity')
        need(sha(raw_bytes)==terminal['raw_sha256'], 'raw hash')
        if not construction:
            freeze_bytes = (source/'FREEZE.json').read_bytes()
            freeze = parse(freeze_bytes)
            need(sha(freeze_bytes)==terminal['freeze_sha256'],'freeze binding')
            for name, digest in freeze['files'].items():
                need(sha((source/name).read_bytes())==digest,'source:'+name)
        pids = []
        for i, row in enumerate(rows):
            rep, scenario, policy = schedule[i]
            tag = str(i)+':'
            need(type(row['index']) is int and row['index']==i,tag+'index')
            need(type(row['returncode']) is int and row['returncode']==0 and row['stderr']=='',tag+'worker exit')
            r = parse(row['stdout']); pids.append(r['pid'])
            need((r['rep'],r['scenario'],r['policy'])==(rep,scenario,policy) and type(r['rep']) is int,tag+'identity')
            cmd = row['command']
            need(Path(cmd[2]).name=='trial.py' and cmd[3:6]==[policy,scenario,str(rep)],tag+'command')
            need(type(r['pid']) is int and r['pid']>0,tag+'pid')
            need(set(r['source_hashes'])=={'candidate.py','consumer.py','trial.py','vendor/image_artifact.py','vendor/exact_gate.py'},tag+'source denominator')
            for n,h in r['source_hashes'].items():
                need(sha((source/n).read_bytes())==h,tag+'worker source:'+n)
            times = r['times']
            seq = [row['start_ns']]+[times[k] for k in ('started','initial_published','maintenance_finished','second_returned','finished')]+[row['end_ns']]
            need(all(type(x) is int for x in seq) and seq==sorted(seq),tag+'clock order')
            a, b = reference(rep), reference(rep,True)
            target = b if scenario in ('FRAME_CHANGED','NEXT_NAME_OCCUPIED') else a
            need(r['frame']=={'width':96,'height':64,'mode':'RGB','pixels_b64':base64.b64encode(target).decode()},tag+'frame')
            before = {k:unb(v) for k,v in r['before'].items()}
            mid = {k:unb(v) for k,v in r['maintained'].items()}
            after = {k:unb(v) for k,v in r['after'].items()}
            need(set(before)=={'001.png'} and decode(before['001.png'])==(96,64,a),tag+'initial pixels')
            initial = r['initial']
            need(initial['receipt']['image_reused'] is False and Path(initial['receipt']['image']).name=='001.png',tag+'initial receipt')
            need(initial['authority']=='none' and initial['model_calls']==0 and initial['input_dispatched'] is False,tag+'initial authority')
            if scenario=='CACHE_MISSING':
                need(mid=={},tag+'missing maintenance')
            elif scenario=='CACHE_TRUNCATED':
                need(mid=={'001.png':before['001.png'][:33]},tag+'truncated maintenance')
            elif scenario=='CACHE_OTHER_PIXELS':
                need(decode(mid['001.png'])==(96,64,b),tag+'pixel maintenance')
            elif scenario=='CACHE_OTHER_GEOMETRY':
                need(decode(mid['001.png'])==(48,128,a),tag+'geometry maintenance')
            elif scenario=='CACHE_LOSSLESS_REENCODED':
                need(decode(mid['001.png'])==(96,64,a) and mid['001.png']!=before['001.png'],tag+'reencoding')
            elif scenario=='NEXT_NAME_OCCUPIED':
                need(mid==dict(before,**{'002.png':SENTINEL}),tag+'collision fixture')
            else:
                need(mid==before,tag+'unchanged maintenance')
            need(all(after.get(k)==v for k,v in mid.items()),tag+'retained files immutable')
            stored = {q.name:q.read_bytes() for q in (root/f'case-{i:02d}'/'images').iterdir() if q.is_file()}
            need(stored==after,tag+'retained disk bytes')
            if scenario=='NEXT_NAME_OCCUPIED':
                need(r['error']=={'type':'FileExistsError','errno':17} and r['result'] is None and r['consumer'] is None,tag+'collision refusal')
                need(after==mid,tag+'collision no overwrite')
                counts[policy+':refused']+=1
                continue
            need(r['error'] is None,tag+'unexpected refusal')
            result = r['result']; receipt = result['receipt']; collector = r['consumer']
            need(result['authority']=='none' and type(result['model_calls']) is int and result['model_calls']==0 and result['input_dispatched'] is False,tag+'authority')
            needed_new = scenario in ('FRAME_CHANGED','CACHE_MISSING') or (policy!='ORIGINAL' and scenario in ('CACHE_TRUNCATED','CACHE_OTHER_PIXELS','CACHE_OTHER_GEOMETRY')) or (policy=='BYTE_PIN_REPAIR' and scenario=='CACHE_LOSSLESS_REENCODED')
            need(type(receipt['image_reused']) is bool and receipt['image_reused'] is (not needed_new),tag+'reuse')
            name = '002.png' if needed_new else '001.png'
            need(Path(receipt['image']).name==name,tag+'returned name')
            need(set(after)==set(mid)|{name},tag+'file denominator')
            need(type(collector['returncode']) is int and collector['returncode']==0 and collector['stderr']=='',tag+'collector exit')
            c = parse(collector['stdout']); pids.append(c['pid'])
            need(Path(collector['command'][4]).name=='consumer.py' and collector['command'][5]==receipt['image'],tag+'collector command')
            data = unb(c['bytes_b64'])
            need(c['path']==receipt['image'] and type(c['size']) is int and c['size']==len(data) and c['sha256']==sha(data),tag+'collector bytes')
            need(data==after[name],tag+'actual file bytes')
            need(times['second_returned']<=c['start_ns']<=c['end_ns']<=times['finished'],tag+'consumer order')
            try:
                exact = decode(data)==(96,64,target)
            except ValueError:
                exact = False
            expected_bad = policy=='ORIGINAL' and scenario in ('CACHE_TRUNCATED','CACHE_OTHER_PIXELS','CACHE_OTHER_GEOMETRY')
            need(exact is (not expected_bad),tag+'scoped expected pixels')
            counts[policy+(':exact' if exact else ':wrong_or_invalid')]+=1
            counts[policy+(':reused' if receipt['image_reused'] else ':created')]+=1
        need(len(pids)==len(set(pids)), 'distinct process identities')
    except Exception as exc:
        errors.append('audit exception:'+repr(exc))
    return {'decision':'PASS_CACHE_MAINTENANCE_CONTRACT_SCOPED' if not errors else 'HOLD_OR_FAIL_AUDIT',
            'errors':errors,'checks':checks,'counts':dict(sorted(counts.items()))}


def audit_all(root, source=None):
    outputs = [audit(root/('batch'+str(rep)),source=source,rep=rep) for rep in (0,1)]
    errors = [str(rep)+':'+error for rep,a in enumerate(outputs) for error in a['errors']]
    counts = Counter()
    for a in outputs:
        counts.update(a['counts'])
    try:
        previous = parse((root/'batch0'/'EXECUTION.json').read_text())
        current = parse((root/'batch1'/'EXECUTION.json').read_text())
        if previous['end_ns'] > current['start_ns']:
            errors.append('batch order')
        for rep in (0,1):
            if not (root/('batch'+str(rep)+'.started')).is_file():
                errors.append('missing consumed marker')
    except Exception as exc:
        errors.append(repr(exc))
    return {'decision':'PASS_CACHE_MAINTENANCE_CONTRACT_SCOPED' if not errors else 'HOLD_OR_FAIL_AUDIT',
            'errors':errors,'cases':48,'batches':2,'checks':sum(a['checks'] for a in outputs),
            'counts':dict(sorted(counts.items()))}


if __name__ == '__main__':
    root = Path(sys.argv[1])
    result = audit(root,construction=True) if '--construction' in sys.argv else audit_all(root)
    print(json.dumps(result,sort_keys=True,indent=2))
    sys.exit(0 if not result['errors'] else 2)
