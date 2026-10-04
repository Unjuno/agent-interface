"""Effective copies of retained data only; never invokes the formal producer."""
import copy
import hashlib
import json
import pathlib
import sys
from audit import audit_records, parse_line


def main():
    raw, output = map(pathlib.Path,sys.argv[1:3])
    output.mkdir(exist_ok=False)
    records = [parse_line(line) for line in raw.read_bytes().splitlines()]
    baseline = audit_records(records)
    if baseline['status'] != 'PASS_FD_LIFETIME_BOUNDARY_SCOPED':
        raise RuntimeError('passing baseline required before testing mutations')
    controls = []
    for name in ('missing_row','float_footer_count','forged_late_close_identity','replacement_byte_as_old_read','missing_after_reuse_witness','second_once_owner_claim','wrong_environment_pin','missing_real_cleanup'):
        altered = copy.deepcopy(records)
        if name == 'missing_row':
            altered.pop(1)
        elif name == 'float_footer_count':
            altered[-1]['rows'] = 6.0
        elif name == 'forged_late_close_identity':
            row = altered[1]
            event = next(e for e in row['events'] if e['kind']=='close_requested' and e['actor']=='worker')
            event['identity'] = row['events'][0]['original_identity']
        elif name == 'replacement_byte_as_old_read':
            next(e for e in altered[1]['events'] if e['kind']=='read_return')['hex'] = '52'
        elif name == 'missing_after_reuse_witness':
            altered[1]['events'] = [e for e in altered[1]['events'] if not(e['kind']=='blocked_observed' and e['label']=='after_reuse')]
            for index,event in enumerate(altered[1]['events']):
                event['seq'] = index
        elif name == 'second_once_owner_claim':
            event = next(e for e in altered[4]['events'] if e['kind']=='close_claim' and e['actor']=='worker')
            event['claimed'],event['fd'] = True,altered[4]['events'][0]['original_fd']
        elif name == 'wrong_environment_pin':
            altered[0]['environment']['executable_sha256'] = '0'*64
        else:
            altered[4]['events'] = [e for e in altered[4]['events'] if e['kind']!='harness_closed']
            for index,event in enumerate(altered[4]['events']):
                event['seq'] = index
        data = json.dumps(altered,sort_keys=True).encode()
        if data == json.dumps(records,sort_keys=True).encode():
            raise RuntimeError('ineffective control '+name)
        (output/(name+'.json')).write_bytes(data)
        try:
            audit_records(json.loads(data))
        except (ValueError,KeyError,TypeError,IndexError) as error:
            controls.append({'name':name,'sha256':hashlib.sha256(data).hexdigest(),'rejection':str(error)})
        else:
            raise RuntimeError('false acceptance '+name)
    summary = {'baseline':baseline['status'],'controls_rejected':len(controls),'controls':controls,'formal_producer_invocations':0}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':
    main()
