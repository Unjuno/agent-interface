"""Recompute primary metrics from post-input oracle records and audit freeze."""
import argparse,hashlib,json,statistics
from pathlib import Path


def analyze(folder):
    root=Path(__file__).resolve().parent.parent
    for relative,expected in json.loads((folder/'freeze.json').read_text()).items():
        assert hashlib.sha256((root/relative).read_bytes()).hexdigest()==expected,relative
    rows=json.loads((folder/'summary.json').read_text())
    assert len(rows)==12 and len({(r['seed'],r['delay_ms'],r['mode']) for r in rows})==12
    for r in rows:
        if r['status']!='ok':continue
        p=folder/f'{r["seed"]}-{r["delay_ms"]}-{r["mode"]}'
        truth=json.loads((p/'oracle.json').read_text());control=json.loads((p/'control.json').read_text())
        last=0;duration=0;error=0;inside=0
        for frame in truth:
            weight=frame['t']-last;assert weight>=0
            actual=abs(frame['player']-frame['target'])
            assert abs(actual-frame['error'])<1e-8
            error+=actual*weight;inside+=(actual<=30)*weight;duration+=weight;last=frame['t']
        assert duration>=6
        assert abs(error/duration-r['mean_error_px'])<1e-8
        assert abs(inside/duration-r['fraction_within_30px'])<1e-8
        assert len(control)==r['capture_count']
        assert sum(x['decision'] for x in control)==r['decision_count']
    groups=[]
    for delay in (250,1000):
        paired=[]
        for seed in range(860201,860204):
            pair={r['mode']:r for r in rows if r['seed']==seed and r['delay_ms']==delay}
            if any(r['status']!='ok' for r in pair.values()):continue
            paired.append(dict(seed=seed,error_local_minus_delayed=pair['local']['mean_error_px']-pair['delayed']['mean_error_px'],
                               within_local_minus_delayed=pair['local']['fraction_within_30px']-pair['delayed']['fraction_within_30px']))
        groups.append(dict(delay_ms=delay,valid_pairs=len(paired),pairs=paired,
            arm_mean_error_px={mode:statistics.mean(r['mean_error_px'] for r in rows if r['delay_ms']==delay and r['mode']==mode and r['status']=='ok') for mode in ('local','delayed')},
            arm_mean_within_30={mode:statistics.mean(r['fraction_within_30px'] for r in rows if r['delay_ms']==delay and r['mode']==mode and r['status']=='ok') for mode in ('local','delayed')}))
    return dict(episodes=len(rows),failed=sum(r['status']!='ok' for r in rows),groups=groups,
                scope='three seeded synthetic trajectories; simulated decision cadence; no inference overlap or LLM measurement')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('folder',type=Path);a=ap.parse_args()
    report=analyze(a.folder);(a.folder/'analysis.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
