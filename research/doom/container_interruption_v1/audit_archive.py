"""Verify and replay the full retained ZIP with the Python standard library."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from occupancy import analyze_program, EvidenceError

HERE=Path(__file__).resolve().parent


def sha(data):return hashlib.sha256(data).hexdigest()
def check(ok,why):
    if not ok:raise EvidenceError(why)


def audit(path):
    reference=json.loads((HERE/'archive.json').read_text())
    data=Path(path).read_bytes()
    check(len(data)==reference['bytes'] and sha(data)==reference['sha256'],'archive integrity failure')
    with zipfile.ZipFile(path) as z:
        def raw(name):return z.read('run-v2/'+name)
        def obj(name):return json.loads(raw(name))
        def rows(name):return [json.loads(x) for x in raw(name).decode().splitlines() if x.strip()]
        m=obj('artifact-manifest.json');plan=obj('plan.json')
        for n,h in m.items():
            b=raw(n);check(len(b)==h['bytes'] and sha(b)==h['sha256'],'raw artifact '+n)
        for n,h in plan['source_sha256'].items():
            check(sha(z.read('source/'+n))==h,'executed source '+n)
            check(sha((HERE/n).read_bytes())==h,'published source '+n)
        base=json.loads(z.read('source-bundle-manifest.json'))
        check(base['base_commit']==plan['base_commit'],'base mismatch')
        results=[]
        for spec in plan['cases']:
            prefix=spec['name']+'/runtime/'
            check(raw(prefix+'events.jsonl')==raw(prefix+'delivered.jsonl'),'delivery divergence')
            for n,h in obj(prefix+'sources.json').items():
                check(base['files']['research/'+n]['sha256']==h,'runtime source '+n)
            events=rows(prefix+'events.jsonl')
            a=[r for r in events if r.get('event')=='accepted']
            t=[r for r in events if r.get('event')=='terminal']
            check(len(a)==len(t)==1,'accepted/terminal count');a,t=a[0],t[0]
            check(t['status']==spec['status'],'terminal status')
            check(sum(r.get('event')=='rejected' for r in events)==1,'stale refusal not exposed')
            check(not any(str(r.get('schema','')).startswith('independent-progress-') for r in events),'scorer leakage')
            occupancy=analyze_program(events,a['id'],a['accepted_ns'],t['terminal_ns'])
            check(occupancy['admission_count']==len(spec['keys']),'planned exposure not observed')
            samples=rows(prefix+'scorer-samples.jsonl')
            final=[r for r in samples if r.get('direct_final_sample') is True]
            check(len(final)==1 and final[0] is samples[-1],'final scorer uniqueness/order')
            score=obj(prefix+'score.json');last=final[0]['payload']
            for key in ('map_exit','episode_finished','player_dead','death_count','kill_count'):
                check(type(score[key]) is type(last[key]) and score[key]==last[key],'terminal agreement '+key)
            check(all(s.get('controller_visible') is False for s in samples),'scorer visibility')
            cause=(t.get('interruption') or {}).get('record');reaction=None
            if spec['status'] in ('cancelled','expired'):
                check(cause is not None and cause['reason']==spec['status'] and cause['verified'] is True,'owner interruption missing')
                trigger=(next(r['requested_ns'] for r in events if r.get('event')=='cancel_requested')
                         if spec['status']=='cancelled' else a['valid_until_ns'])
                reaction=(cause['verified_ns']-trigger)/1e6
            results.append({'case':spec['name'],'status':t['status'],'window_ms':occupancy['window_ns']/1e6,
                'retained_lower_ms':occupancy['retained_lower_ns']/1e6,'retained_upper_ms':occupancy['retained_upper_ns']/1e6,
                'trigger_to_empty_ms':reaction,'scorer_missed_periods':sum(s.get('missed_periods_before',0) for s in samples)})
            if spec['name']=='normal-chord':
                bad=[r for r in events if r.get('event')!='input_release_transition']
                try:analyze_program(bad,a['id'],a['accepted_ns'],t['terminal_ns'])
                except EvidenceError:pass
                else:raise EvidenceError('missing-release mutation passed')
    return {'schema':'container-interruption-full-archive-audit-v1','pass':True,
            'raw_files_verified':len(m),'cases':results,'archive_sha256':reference['sha256'],
            'scope':'full retained file integrity and timing/scorer replay; no gameplay efficacy claim'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('archive',type=Path);a=ap.parse_args()
    print(json.dumps(audit(a.archive),indent=2))

if __name__=='__main__':main()
