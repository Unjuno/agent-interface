"""Post-run saved-evidence qualification, not a repair or formal rerun."""
import copy, hashlib, json
from pathlib import Path
from auditor import canonical, validate_packet
ROOT = Path(__file__).parent
def strict(row, record):
    validate_packet(row, record)
    if canonical(row['packet']['meta']) != canonical(record['meta']):
        raise ValueError('typed metadata')
    p = row['packet']['payload']; policy = row['policy']
    if policy == 'RAW_CHECKPOINT':
        if canonical(p) != canonical(record['observation']):
            raise ValueError('typed observation')
    else:
        if type(p['v']) is not bool: raise ValueError('typed verified')
        if policy != 'RECEIPT_TRUST':
            if type(p['k']) is not int or type(p['b']) is not int:
                raise ValueError('typed bit fields')
        if policy == 'CONSERVATIVE_PROFILE' and type(p['o']) is not bool:
            raise ValueError('typed residual')
    for key, value in row['decision'].items():
        if value is not None and type(value) is not bool:
            raise ValueError('typed decision')
    return True
def main():
    raw=(ROOT/'runs/candidate/evidence/packets.jsonl').read_bytes()
    records={r['case_id']:r for r in json.loads((ROOT/'INPUT.json').read_text())['records']}
    rows=[json.loads(line) for line in raw.splitlines()]
    for row in rows: strict(row,records[row['case_id']])
    source=next(r for r in rows if r['policy']=='CONSERVATIVE_PROFILE')
    checks=[]
    for target,key in [('payload','v'),('decision','owned_up')]:
        row=copy.deepcopy(source)
        part=row['packet']['payload'] if target=='payload' else row['decision']
        part[key]=int(part[key]); wire=canonical(row['packet'])
        row.update(bytes=len(wire),wire_hex=wire.hex())
        try: strict(row,records[row['case_id']]); rejected=False
        except ValueError: rejected=True
        checks.append({'target':target,'rejected':rejected})
    assert len(rows)==200 and all(c['rejected'] for c in checks)
    result={'status':'PASS_SAVED_TYPED_CORPUS_ONLY','saved_packets':len(rows),
            'copied_type_controls':checks,'packets_sha256':hashlib.sha256(raw).hexdigest(),
            'native_inputs':0,'formal_candidate_invocations':0,'formal_auditor_invocations':0,
            'original_auditor_repaired':False,'first_scientific_result':'FAIL_PACKET_BYTE_GATE'}
    with (ROOT/'validation/strict_saved.json').open('x') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
