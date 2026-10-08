from __future__ import annotations
import hashlib,json
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent
ABI=ROOT/'inkscape_authority_ended_abi_v2'
INPUT=H/'audit_input.json'
BRIDGE=ABI/'authority_ended_bridge_v2.py'
NORMALIZER=ABI/'post_authority_normalize_v2.py'

def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git_blob(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

i=json.loads(INPUT.read_text())
if i.get('schema')!='inkscape-abi-v2-provenance-reaudit-v1-input':
    raise SystemExit('INPUT_SCHEMA_MISMATCH')
if i.get('captured_from_main')!='227ba648f1c0b83e9a5b69f4e0c7d39839d3578f':
    raise SystemExit('INPUT_BASE_MISMATCH')

rows=[]
def add(case,passed,detail): rows.append({'case':case,'pass':bool(passed),'detail':detail})

current=i['current_sources']; claims=i['manifest']['claimed_formal_sha256']; build=i['build_candidate']['expected_candidate_sha256']
bridge_sha=sha256(BRIDGE); bridge_blob=git_blob(BRIDGE)
normalizer_sha=sha256(NORMALIZER); normalizer_blob=git_blob(NORMALIZER)

add('current_bridge_identity_recomputed',
    bridge_sha==current['authority_ended_bridge_v2.py']['sha256'] and bridge_blob==current['authority_ended_bridge_v2.py']['git_blob'],
    {'sha256':bridge_sha,'git_blob':bridge_blob})
add('current_normalizer_identity_recomputed',
    normalizer_sha==current['post_authority_normalize_v2.py']['sha256'] and normalizer_blob==current['post_authority_normalize_v2.py']['git_blob'],
    {'sha256':normalizer_sha,'git_blob':normalizer_blob})
add('manifest_formal_claims_mismatch_current_sources',
    bridge_sha!=claims['authority_ended_bridge_v2.py'] and normalizer_sha!=claims['post_authority_normalize_v2.py'],
    {'current_bridge':bridge_sha,'claimed_bridge':claims['authority_ended_bridge_v2.py'],'current_normalizer':normalizer_sha,'claimed_normalizer':claims['post_authority_normalize_v2.py']})
add('build_gate_reuses_stale_manifest_claims',
    build==claims and build['authority_ended_bridge_v2.py']!=bridge_sha and build['post_authority_normalize_v2.py']!=normalizer_sha,
    {'build_expected':build,'manifest_claimed':claims})
formal=i['formal_commit_observation']
add('bridge_absent_at_formal_evidence_commit',
    formal.get('formal_evidence_commit')=='38f40605e6131d9695e1b3b3b789512819affb29' and formal.get('bridge_path_at_formal_commit')=='404_not_found',
    {'formal_commit':formal.get('formal_evidence_commit'),'observation':formal.get('bridge_path_at_formal_commit')})
add('normalizer_absent_at_formal_evidence_commit',
    formal.get('formal_evidence_commit')=='38f40605e6131d9695e1b3b3b789512819affb29' and formal.get('normalizer_path_at_formal_commit')=='404_not_found',
    {'formal_commit':formal.get('formal_evidence_commit'),'observation':formal.get('normalizer_path_at_formal_commit')})
chain=i['original_commit_chain']
chain_ok=(
    len(chain)==3
    and chain[0]['sha']=='38f40605e6131d9695e1b3b3b789512819affb29'
    and chain[1]['sha']=='9ca8fbbb8117290037d0a50f277ee189adc1cb0a'
    and chain[1]['parent']==chain[0]['sha']
    and chain[2]['sha']=='08e176fb187b7075695be7d51a470fd9fca750ed'
    and chain[2]['parent']==chain[1]['sha']
)
add('formal_evidence_precedes_both_source_add_commits',chain_ok,{'chain':chain})
add('reconciled_main_retains_postformal_source_blobs',
    i['captured_from_main']=='227ba648f1c0b83e9a5b69f4e0c7d39839d3578f'
    and bridge_blob=='63639f44eba47a2842e57e3761730e6f6224e815'
    and normalizer_blob=='a6eb2b8a8964b34ac22dd4f1cbeaaff879f7e5b1',
    {'main':i['captured_from_main'],'bridge_git_blob':bridge_blob,'normalizer_git_blob':normalizer_blob})

passed=len(rows)==8 and all(r['pass'] for r in rows)
out={
    'schema':'inkscape-abi-v2-provenance-reaudit-v1-formal-result',
    'result_id':'inkscape-abi-v2-provenance-reaudit-v1-20260916-01',
    'base_commit':'227ba648f1c0b83e9a5b69f4e0c7d39839d3578f',
    'rows':rows,
    'hard_gate_pass':passed,
    'decision':'INVALIDATE_ABI_V2_FORMAL_SOURCE_PROVENANCE_REQUIRE_RERUN' if passed else 'PROVENANCE_HYPOTHESIS_NOT_ESTABLISHED',
    'formal_retries':0,
    'source_sha256':{
        'audit_input.json':sha256(INPUT),
        'formal_runner.py':sha256(H/'formal_runner.py'),
        'current_authority_ended_bridge_v2.py':bridge_sha,
        'current_post_authority_normalize_v2.py':normalizer_sha,
    },
    'scope':{
        'invalidated':'old ABI-v2 live formal claim as source-bound/reconstructible evidence',
        'not_invalidated_by_this_test':['bridge-v2 semantic contract','offline contract evidence','historical raw terminal/observation data'],
    },
    'limitations':['GitHub absence/commit-chain/manifest/build observations are frozen in audit_input.json','exact formal-run source bytes could exist outside canonical Git history','timing labels are separate and non-gating'],
}
(H/'formal-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if passed else 2)
