import ast
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'session_map01_v19.py'
source=SOURCE.read_text(encoding='utf-8')
source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
module=ast.parse(source)
fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='_capture_backend')
namespace={}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(SOURCE),'exec'),namespace)
capture=namespace['_capture_backend']

class Backend:
    def __init__(self,session,out,emit,signal_readers):
        self.emit=emit
        self.held=set()

def probe(admission_order,release_order):
    events=[]; state={}
    backend=capture(Backend,state)(None,None,events.append,None)
    ids={key:{'id':'program','step':0,'owner_id':'owner','intent_token':'intent','key':key,'actuation_id':'act-'+key} for key in admission_order}
    for key in admission_order:
        backend.held.add(key)
        backend.emit({'event':'input_admission',**ids[key]})
    for key in release_order:
        backend.held.remove(key)
        backend.emit({'event':'input_release_measurement',**ids[key]})
    candidate=state.get('candidate')
    if candidate is None:
        return {'admission_order':admission_order,'release_order':release_order,'candidate':'none','matched':False}
    down,up,held_after=candidate
    identity=('id','step','owner_id','intent_token','key','actuation_id')
    match=all(down.get(field)==up.get(field) for field in identity) and held_after==[]
    return {'admission_order':admission_order,'release_order':release_order,
      'candidate_down_key':down['key'],'candidate_up_key':up['key'],
      'held_after':held_after,'matched':match}

cases=[]
for n in (1,2,3):
    keys=[chr(ord('A')+i) for i in range(n)]
    rows=[probe(list(a),list(r)) for a in itertools.permutations(keys) for r in itertools.permutations(keys)]
    matched=sum(row['matched'] for row in rows)
    cases.append({'key_count':n,'schedule_count':len(rows),'matched_pairs':matched,
                  'censored_no_pair':len(rows)-matched,'match_rate':matched/len(rows),
                  'schedules':rows})
result={'schema':'issue59-pr7692-release-order-probe-a01','kind':'offline_construction_exhaustion',
 'source':{'pr':7692,'head':'7ec4e3ef405919bf5f1bfd9eeddbe630f3a5b32e',
  'path':'research/doom/session_map01_v19.py','git_blob_sha1':'93acee5927751fcf3b4eabadc24efe3dc4483b80',
  'local_sha256':source_sha256},
 'hypothesis':'The exact V19 _capture_backend wrapper retains only the most recent admission. For simultaneous N-key holds, its final empty-state release pair is measurable only when the last-admitted key is also the last-released key; other release orders are safely censored as no matching pair.',
 'decision_rule':'PASS_SCOPED if exact-source schedule enumeration matches 1/N of N-key release permutations for N=1..3, every captured candidate has empty held state, and every non-match is an identity mismatch rather than a false match.',
 'cases':cases,
 'limits':'Synthetic backend state only. No physical keys, X server, game, planner, feedback, recovery, or allocation. The probe assesses optional tail measurement availability, not actuator safety or task control. It does not establish how often overlapping keys occur in live V39 programs.',
 'decision':'PASS_SCOPED: measured-tail availability depends on release order for overlapping multi-key programs. Existing head tests cover one mismatched pair and classify it as CENSORED/no_matched_release_pair, but do not exhaust multi-key release orders.'}
( ROOT/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{k:v for k,v in c.items() if k!='schedules'} for c in cases],indent=2))
