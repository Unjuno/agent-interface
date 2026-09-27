import copy, json
from pathlib import Path
from common import validate_fixture
ROOT=Path(__file__).resolve().parent
base=json.loads((ROOT/'fixture.json').read_text())
controls=[]
def expect_reject(name, mut):
    f=copy.deepcopy(base); mut(f)
    rejected=False
    try: validate_fixture(f)
    except Exception: rejected=True
    controls.append({'name':name,'rejected':rejected})
expect_reject('source_blob_substitution', lambda f: f.__setitem__('source_git_blob','0'*40))
expect_reject('phase_substitution_repeat_A', lambda f: f.__setitem__('horizon_phases',['layout_change','repeat_A']))
expect_reject('persistent_route_substitution', lambda f: f['arms']['persistent']['routes'].__setitem__(3,'cold'))
expect_reject('ephemeral_route_substitution', lambda f: f['arms']['ephemeral']['routes'].__setitem__(4,'reuse'))
expect_reject('repeat_B_model_injection', lambda f: f['arms']['persistent']['repeat_B'].__setitem__('input_tokens',1))
out={'schema':'integrated_efficiency_post_repair_payback_corruption_v1','controls':controls,'all_rejected':all(x['rejected'] for x in controls)}
(ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if not out['all_rejected']: raise SystemExit(1)
print(json.dumps(out,sort_keys=True))
