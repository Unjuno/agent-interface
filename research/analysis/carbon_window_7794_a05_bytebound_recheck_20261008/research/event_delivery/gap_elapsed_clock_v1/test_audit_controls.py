"""Mutation checks operate only on temporary copies of retained evidence."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile
import audit


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')


def mutate(root: Path, schedule: dict, name: str) -> None:
    case = next(x for x in schedule['cases'] if x['scenario']=='permanent' and x['policy']=='OBS_COUNT_3')
    folder = root/case['id']
    if name == 'missing_case':
        shutil.rmtree(folder)
        return
    if name == 'boolean_invocation_count':
        path=root/'invocation.json'; data=json.loads(path.read_text()); data['invocations']=True
        write_json(path,data); return
    if name == 'lost_process_exit':
        path=folder/'case.json'; data=json.loads(path.read_text()); del data['exits']['consumer']
        write_json(path,data); return
    if name == 'database_byte_change':
        path=folder/'state.sqlite3'; data=bytearray(path.read_bytes()); data[-1]^=1
        path.write_bytes(data); return
    path=folder/'journal.jsonl'; rows=[json.loads(x) for x in path.read_text().splitlines()]
    if name=='missing_journal_row':
        del rows[2]
    elif name=='duplicate_request_id':
        request=json.loads(rows[2]['request_line'])
        request['request_id']=json.loads(rows[1]['request_line'])['request_id']
        rows[2]['request_line']=json.dumps(request)+'\n'
    elif name=='implicit_ack_advance':
        rows[1]['after']['ack'][0][0]=3
    elif name=='missing_terminal_lf':
        rows[1]['response_line']=rows[1]['response_line'].rstrip('\n')
    else:
        for row in rows:
            response=json.loads(row['response_line'])
            changed=False
            for step in response.get('steps',[]):
                if name=='boolean_observation_count' and 'state' in step:
                    step['state']['count']=True; changed=True
                elif name=='authority_upgrade' and step.get('state',{}).get('receipt'):
                    step['state']['receipt']['authority']=True; changed=True
                elif name=='receipt_identity_change' and step.get('state',{}).get('receipt'):
                    step['state']['receipt']['key'][0]=9; changed=True
                if changed:
                    break
            if changed:
                row['response_line']=json.dumps(response,separators=(',',':'))+'\n'
                break
        else:
            raise ValueError('mutation target not found: '+name)
    path.write_text(''.join(json.dumps(row,separators=(',',':'))+'\n' for row in rows))


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,required=True)
    p.add_argument('--schedule',type=Path,required=True); p.add_argument('--freeze',type=Path)
    p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    baseline=audit.audit(a.root,a.schedule,a.freeze)
    if baseline['status']!='PASS_LOCAL_CLOCK_BOUNDARY_SCOPED':
        raise RuntimeError('unmodified baseline must pass before mutation controls')
    names=['missing_case','missing_journal_row','duplicate_request_id','boolean_invocation_count',
           'boolean_observation_count','authority_upgrade','receipt_identity_change','implicit_ack_advance',
           'lost_process_exit','database_byte_change','missing_terminal_lf']
    schedule=json.loads(a.schedule.read_text()); rows=[]
    with tempfile.TemporaryDirectory(prefix='gap-audit-control-') as temp:
        for name in names:
            target=Path(temp)/name; shutil.copytree(a.root,target)
            mutate(target,schedule,name)
            result=audit.audit(target,a.schedule,a.freeze)
            rows.append({'mutation':name,'rejected':bool(result['errors']),
                         'status':result['status'],'errors':result['errors']})
    result={'baseline':baseline['status'],'controls':rows,'rejected':sum(x['rejected'] for x in rows),
            'planned':len(names),'original_evidence_modified':False}
    with a.out.open('x') as f:
        f.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='controls'}))
    return 0 if all(x['rejected'] for x in rows) else 2

if __name__=='__main__':
    raise SystemExit(main())
