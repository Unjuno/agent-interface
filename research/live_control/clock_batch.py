"""Lossless batch representation for one shared raw-event clock domain.

This is an offline candidate codec, not input authority or a runtime protocol.
"""
import json


def clone(value):return json.loads(json.dumps(value,allow_nan=False))


def pack(records):
    if not isinstance(records,list):raise ValueError('record list required')
    copied=clone(records)
    if any(not isinstance(r,dict) or 'clock_domain_id' not in r for r in copied):raise ValueError('explicit record clock fields required')
    domain=copied[0]['clock_domain_id'] if copied else None
    if domain is not None and (not isinstance(domain,str) or not domain):raise ValueError('clock identity or explicit null required')
    if any(r['clock_domain_id']!=domain for r in copied):raise ValueError('mixed domains require separate batches')
    for record in copied:del record['clock_domain_id']
    return dict(format='clock-batch-v1',clock_domain_id=domain,records=copied)


def unpack(batch):
    if not isinstance(batch,dict) or set(batch)!={'format','clock_domain_id','records'} or batch['format']!='clock-batch-v1':raise ValueError('clock batch schema required')
    domain=batch['clock_domain_id'];records=batch['records']
    if domain is not None and (not isinstance(domain,str) or not domain):raise ValueError('clock identity or explicit null required')
    if not isinstance(records,list) or any(not isinstance(r,dict) or 'clock_domain_id' in r for r in records):raise ValueError('invalid batch records')
    copied=clone(records)
    for record in copied:record['clock_domain_id']=domain
    return copied
