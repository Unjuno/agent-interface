"""Characterize exact review copies; imports auditors/tests, never a producer."""
import hashlib
import json
from pathlib import Path
import audit as v1
import audit_v2 as v2
from test_audit_v2 import RAW, FREEZE, witness

EXPECTED = {
    'outside-wrapper-row0':'a1d092b852107ad006a3ce1a76cf97f80560c360c8f40356cd9cefce2343a8ef',
    'outside-wrapper-row4':'f834767d601ac6532326fa8de79519de1bcaff2ed0ccf0a6e9b3341d7f60a7ae',
    'committee-deliver-before-wrapper':'5d8d76760f1cd07ccc96d71f1a5b31e43837e43837f7a831501fff06bd6e85b1',
    'committee-submit-before-request':'921a3cf8c483c70ef4a025e6cddc3bd60939e3ff51b28dae58191f24b3feb8fe',
    'committee-wrong-caller-role':'d35f67d4ddb569117ad913bec7b1cf3351109a44c78c30585a5d7ee5e8143ec0',
}

def require(value,message):
    if not value:
        raise ValueError(message)

def main():
    root = Path(__file__).resolve().parent
    out = root/'evidence/audit-v2-witnesses'
    out.mkdir(exist_ok=False)
    controls = []
    for name,expected in EXPECTED.items():
        changed = witness(name)
        data = (json.dumps(changed,indent=2)+'\n').encode()
        checksum = hashlib.sha256(data).hexdigest()
        require(checksum == expected,'exact review witness identity: '+name)
        with (out/(name+'.json')).open('xb') as stream:
            stream.write(data)
        legacy = v1.verify(changed,FREEZE)
        repaired = v2.verify(changed,FREEZE)
        require(not legacy['errors'] and repaired['errors'],'review comparison: '+name)
        controls.append(dict(witness=name,raw_sha256=checksum,v1_disposition=legacy['disposition'],
            v1_errors=legacy['errors'],v2_disposition=repaired['disposition'],v2_errors=repaired['errors']))
    original = v2.verify(RAW,FREEZE)
    require(not original['errors'],'unchanged raw')
    old_controls = v2.mutation_controls(RAW,FREEZE)
    require(all(old_controls),'old eight controls retained')
    result = dict(status='PASS_RETAINED_AUDIT_V2_CHARACTERIZATION',review_witnesses=controls,
        original_summaries=original['summaries'],original_disposition=original['disposition'],
        original_eight_controls_reject=old_controls,producer_invocations=0,old_allocation_replays=0,
        independent_nonauthor_review=False)
    with (root/'evidence/audit-v2-witnesses.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
