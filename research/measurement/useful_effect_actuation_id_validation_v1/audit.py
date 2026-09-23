from __future__ import annotations
import hashlib,json
from pathlib import Path
from interval_contract import Actuation,EffectEvent,Interval,ReleaseReceipt,analyze
from id_validation import analyze_validated
ROOT=Path(__file__).resolve().parent
R=json.loads((ROOT/'FORMAL_RESULT.json').read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
errors=[]
for n,h in R['source_sha256'].items():
    if sha(n)!=h: errors.append(f'hash:{n}')
if R['parent_git_blob']!='979f257b4f02be80bcaa30ae8d5a0aa92162bfb1': errors.append('parent_blob')
if R['parent_sha256']!='9783b3b6b24bcb93b4cf608db2bbd3f65740a1b0f5372c783f6c0367b680fc8b': errors.append('parent_sha')
if (R['formal_invocations'],R['formal_reruns'])!=(1,0): errors.append('invocation')
if R['valid_exact_equal']!=R['valid_cases'] or R['valid_cases']!=50000: errors.append('valid')
if R['malformed_rejected']!=R['malformed_cases'] or R['malformed_cases']!=50000: errors.append('malformed')
if any(R[k]!=0 for k in ['authority_actions','task_input_actions','network_actions','model_calls']): errors.append('side_effect')
if R['disposition']!='PASS_ACTUATION_ID_VALIDATION_SCOPED': errors.append('disposition')
# Independent edge controls, not the frozen formal corpus.
W=Interval(0,50)
def A(x): return Actuation(5,ReleaseReceipt(10,12,False),[],x)
def E(x,useful=True): return EffectEvent(7,x,True,useful)
# Parent ambiguity is real.
if analyze(W,[A(None)],[E(None)])['effects']['useful_bound']!=1: errors.append('defect_not_reproduced')
# Candidate fails malformed IDs closed.
for bad in (None,'',0,False,3.14,b'x',('x',)):
    try: analyze_validated(W,[A(bad)],[E(bad)])
    except ValueError: pass
    else: errors.append(f'act_escape:{bad!r}')
for bad in ('',0,False,3.14,b'x',('x',),['x'],{'x':1}):
    try: analyze_validated(W,[A('ok')],[E(bad)])
    except ValueError: pass
    else: errors.append(f'effect_escape:{bad!r}')
# None effect remains valid unbound.
got=analyze_validated(W,[A('ok')],[E(None)])['effects']
if got['useful_unbound']!=1 or got['useful_bound']!=0: errors.append('none_unbound')
out={'task':R['task'],'passed':not errors,'errors':errors,'result_sha256':sha('FORMAL_RESULT.json'),'formal_rerun_executed':False}
(ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
