"""Effective, well-formed raw-evidence mutations; no scientific actors invoked."""
import copy
import json
from pathlib import Path
import sys
from audit import audit_document


def variants(doc):
    out = []
    def add(name, change):
        edited=copy.deepcopy(doc);change(edited);out.append((name,edited))
    add('decision', lambda d:d['rows'][0]['decision'].update(status='REFUSED'))
    add('cookie', lambda d:d['rows'][0]['decision']['basis'].update(cookie=999))
    add('prepared_rows', lambda d:d['rows'][0]['preparation'].update(rows=[[9,9,9]]))
    add('trigger_definition', lambda d:d['rows'][0]['decision']['basis'].update(triggers=[]))
    add('boolean_exit', lambda d:d['rows'][0]['processes']['reader'].update(exit=False))
    add('missing_row', lambda d:d['rows'].pop())
    add('duplicate_row', lambda d:d['rows'].append(copy.deepcopy(d['rows'][0])))
    add('observed_effect', lambda d:d['rows'][0]['observations']['final'].update(effects=[]))
    return out


def controls(path):
    original=json.loads(path.read_text());baseline=audit_document(original,path.parent)
    if baseline['errors']:
        raise ValueError('INTACT_BASELINE_REJECTED')
    rows=[]
    for name,edited in variants(original):
        changed=json.dumps(edited,sort_keys=True)!=json.dumps(original,sort_keys=True)
        r=audit_document(edited,path.parent)
        rows.append({'name':name,'changed':changed,'rejected':bool(r['errors']),'errors':r['errors']})
    return {'baseline_errors':baseline['errors'],'controls':rows,
            'pass':all(r['changed'] and r['rejected'] for r in rows)}


if __name__=='__main__':
    out=controls(Path(sys.argv[1]));text=json.dumps(out,sort_keys=True,indent=2)+'\n'
    if len(sys.argv)>2:
        with Path(sys.argv[2]).open('x') as f:f.write(text)
    print(text,end='');raise SystemExit(not out['pass'])
