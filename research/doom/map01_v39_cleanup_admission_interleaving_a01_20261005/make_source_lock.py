import hashlib,json,subprocess
from pathlib import Path
repo=Path('/Users/taka/Documents/Codex/2026-10-03/new-chat-6/work/pr7805-admission-race-probe')
paths=[
 'research/doom/map01_v39_cancel_release_fix_a01_20261005/bridge_v2_candidate.py',
 'research/doom/map01_v39_cancel_release_fix_a01_20261005/input_owner_v13_candidate.py',
 'research/doom/map01_v39_cancel_release_fix_a01_20261005/test_cancel_release.py',
 'research/doom/map01_v39_perkey_bridge_a01/test_bridge.py',
 'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py',
 'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/test_input_owner_v12.py',
]
heads=['84148054938965dc245602e37220586e07c6f28e','39264f167f8f7541aaf10c43d287938b1317f520']
sets={}
for head in heads:
    blobs={}
    for p in paths:
        data=subprocess.check_output(['git','-C',str(repo),'show',f'{head}:{p}'])
        blobs[p]=hashlib.sha256(data).hexdigest()
    sets[head]=blobs
runners=['A01_probe.py','A02_probe.py','A03_probe.py']
value={'repository':'Unjuno/agent-interface','pr':7805,'source_sets':sets,'runner_sha256':{n:hashlib.sha256((Path(__file__).parent/'attempts'/n).read_bytes()).hexdigest() for n in runners}}
(Path(__file__).with_name('SOURCE_LOCK.json')).write_text(json.dumps(value,indent=2)+'\n')
