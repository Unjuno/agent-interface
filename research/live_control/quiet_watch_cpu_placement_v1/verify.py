#!/usr/bin/env python3
"""Offline-only source, raw, and result verification. Does not run the experiment."""
import hashlib, json
from pathlib import Path
import audit, codec

def main():
    root=Path(__file__).resolve().parent
    freeze=json.loads((root/'freeze.json').read_text())
    for name,digest in freeze['sha256'].items():
        audit.require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'source: '+name)
    exact=codec.unpack(root/'raw')
    raw=json.loads(exact)
    computed=audit.inspect(raw,json.loads((root/'plan.json').read_text()),freeze)
    stored=json.loads((root/'result.json').read_text())
    for key in ('integrity_pass','decision','median_other_same_ratio','pairs_at_or_below_ratio','same_median_max_ns','arms','pairs'):
        audit.require(stored[key]==computed[key],'stored derivative: '+key)
    audit.require(hashlib.sha256(exact).hexdigest()==stored['raw_sha256'],'result raw identity')
    audit.require(len(raw['blocks'])==stored['blocks'],'stored blocks')
    audit.require(sum(len(x['samples']) for x in raw['blocks'])==stored['tuples'],'stored tuples')
    print(json.dumps({'pass':True,'decision':computed['decision'],'blocks':stored['blocks'],
                      'tuples':stored['tuples'],'raw_bytes':len(exact),'raw_sha256':stored['raw_sha256']},sort_keys=True))

if __name__=='__main__': main()
