"""Independent standard-library audit of the compact numeric measurement ledger.

The ledger is lossless for listed numeric endpoints, not a replacement for full
controller/source/image evidence. Timestamps are signed offsets from accepted_ns.
"""
import argparse, hashlib, json, lzma, statistics
from pathlib import Path


def audit(path):
    ledger=json.loads(lzma.decompress(Path(path).read_bytes()));pairs={};total=0;finals=0;counts={};costs={}
    fields=ledger['columns'];ix={v:i for i,v in enumerate(fields)}
    for c in ledger['cases']:
        costs[c['id']]=0;pre=[];lastkill=None;positive=[];final_count=0
        for row in c['acquisitions']:
            r=dict(zip(fields,row));total+=1
            if not r['scheduled']<=r['start']<=r['diag_start']<=r['observed']<=r['diag_end']<=r['end']:raise ValueError('invalid acquisition')
            if not r['diag_start']<=r['refresh_start']<=r['refresh_end']<=r['diag_end']:raise ValueError('invalid refresh bracket')
            if lastkill is not None and r['kills']>lastkill:positive.append(r['observed'])
            lastkill=r['kills']
            if r['observed']<=c['deadline']:
                pre.append(r['tic_after'])
                if r['refresh_called']:costs[c['id']]+=r['refresh_end']-r['refresh_start']
            if r['final']:
                final_count+=1
                if row is not c['acquisitions'][-1]:raise ValueError('final not last')
                expected=[c['score'][k] for k in ['kill_count','death_count','episode_finished','player_dead','map_exit']]
                if [r[k] for k in ['kills','deaths','finished','dead','exit']]!=expected:raise ValueError('score mismatch')
        if final_count!=1:raise ValueError('final uniqueness')
        if not c['release_verified'] or c['keys_down'] or c['buttons_down']:raise ValueError('release not empty')
        if c['terminal_status']!='expired' or c['verified_empty']<c['deadline']:raise ValueError('expiry evidence')
        finals+=1;counts[c['id']]={'source_tics':len(set(pre)),'positive_before_deadline':any(t<=c['deadline'] for t in positive)}
        for sent,received in c['commands']:
            if received<sent:raise ValueError('negative command dispatch')
        pairs.setdefault(c['rep'],{})[c['mode']]=costs[c['id']]
    ratios=[v['refresh5']/v['refresh10'] for _,v in sorted(pairs.items())]
    return {'cases':len(ledger['cases']),'valid_acquisitions':total,'valid_finals':finals,
        'paired_ratio_median':statistics.median(ratios),'paired_ratios':ratios,
        'before_deadline':counts,'ledger_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('ledger',type=Path);a=p.parse_args();print(json.dumps(audit(a.ledger),indent=2))
