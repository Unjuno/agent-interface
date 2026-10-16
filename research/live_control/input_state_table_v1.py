"""Lossless JSON-value table for selected observation input-state fields.

Companion to the full receipt, not a replacement for observation/image/error review.
Unknown nested state fields are preserved. No safety or task-success classification.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

FIELDS = ('input_state_before','input_state_after','input_state_scope','owner_revision_unchanged')


def canonical(value):
    # Distinguish true from 1, 1 from 1.0, missing from null; disallow non-JSON floats.
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def common(objects):
    if not objects:
        return {}
    return {key: copy.deepcopy(value) for key,value in objects[0].items()
            if all(key in obj and canonical(obj[key])==canonical(value) for obj in objects[1:])}


def selected(report):
    rows=[]
    for exchange_index,exchange in enumerate(report.get('exchanges',[])):
        for record_index,event in enumerate(exchange.get('reply',{}).get('records',[])):
            if event.get('event') != 'observation':
                continue
            rows.append(dict(path=['exchanges',exchange_index,'reply','records',record_index],
                             sequence=event.get('sequence'),
                             fields={key:copy.deepcopy(event[key]) for key in FIELDS if key in event}))
    return rows


def encode(rows):
    canonical(rows)
    samples=[r['fields'][key] for r in rows for key in FIELDS[:2]
             if isinstance(r['fields'].get(key),dict)]
    shared=common(samples)
    metadata=common([{k:v for k,v in r['fields'].items() if k not in FIELDS[:2]} for r in rows])
    encoded=[]
    for row in rows:
        fields={k:copy.deepcopy(v) for k,v in row['fields'].items() if k not in metadata}
        for key in FIELDS[:2]:
            if key in fields and isinstance(fields[key],dict):
                fields[key]={'delta':{k:v for k,v in fields[key].items() if k not in shared}}
            elif key in fields:
                fields[key]={'literal':fields[key]}
        encoded.append(dict(path=row['path'],sequence=row['sequence'],fields=fields))
    return dict(common_state=shared,common_observation=metadata,observations=encoded)


def decode(table):
    rows=[]
    for row in table['observations']:
        fields=copy.deepcopy(table['common_observation'])
        fields.update(copy.deepcopy(row['fields']))
        for key in FIELDS[:2]:
            if key not in fields:
                continue
            value=fields[key]
            if set(value)=={'delta'}:
                fields[key]=dict(copy.deepcopy(table['common_state']),**value['delta'])
            elif set(value)=={'literal'}:
                fields[key]=value['literal']
            else:
                raise ValueError('invalid encoded state')
        rows.append(dict(path=row['path'],sequence=row['sequence'],fields=fields))
    return rows


def build(data):
    report=json.loads(data)
    rows=selected(report);table=encode(rows)
    if canonical(decode(table))!=canonical(rows):
        raise ValueError('lossless round trip failed')
    return dict(format='input-state-table-v1',source_sha256=hashlib.sha256(data).hexdigest(),
                table=table,coverage='Four named input-state fields of every exchange observation; all other fields/events/images remain in the original report and receipt.',
                authority='none; historical values only; no attention cleared, lease renewed, or task success inferred')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);args=parser.parse_args()
    from report_pages_v2 import MAX_SOURCE
    with args.source.open('rb') as stream:data=stream.read(MAX_SOURCE+1)
    if len(data)>MAX_SOURCE:raise ValueError('report exceeds bound')
    print(json.dumps(build(data),ensure_ascii=False,allow_nan=False))
