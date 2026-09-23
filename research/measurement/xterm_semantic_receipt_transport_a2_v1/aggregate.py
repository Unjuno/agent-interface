#!/opt/pyvenv/bin/python3
import argparse,json,pathlib,statistics

def pct(vals,p):
    s=sorted(vals); k=(len(s)-1)*p; a=int(k); b=min(a+1,len(s)-1); f=k-a; return s[a]*(1-f)+s[b]*f

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dir',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); d=pathlib.Path(a.dir)
    batches=[json.loads((d/f'BATCH_{i}.json').read_text()) for i in range(4)]
    expected=[]; rows=[]
    for i,b in enumerate(batches):
        exp=list(range(i*5,(i+1)*5)); assert b['batch']==i and b['pairs']==exp and len(b['rows'])==10
        expected += exp; rows += b['rows']
    assert expected==list(range(20)) and len(rows)==40
    by={tr:[r for r in rows if r['transport']==tr] for tr in ['file','dgram']}
    stats={}
    for tr,rr in by.items():
        stats[tr]={
          'n':len(rr),
          'drain_median_ms':statistics.median(r['drain_ms'] for r in rr),
          'drain_p95_ms':pct([r['drain_ms'] for r in rr],0.95),
          'drain_max_ms':max(r['drain_ms'] for r in rr),
          'transport_median_ms':statistics.median(r['transport_seen_ms'] for r in rr),
          'transport_p95_ms':pct([r['transport_seen_ms'] for r in rr],0.95),
          'transport_max_ms':max(r['transport_seen_ms'] for r in rr),
          'integrity':sum(1 for r in rr if r['focus_match'] and r['press_before_frontier'] and r['input_byte_hex']=='78' and r['receipt_valid'] and not r['terminal_key_down'] and r['xterm_rc']==0)
        }
    diffs=[]
    for gid in range(20):
        f=next(r for r in rows if r['case_id']==f'p{gid:03d}-file'); u=next(r for r in rows if r['case_id']==f'p{gid:03d}-dgram'); diffs.append(f['drain_ms']-u['drain_ms'])
    out={'pairs':20,'rows':rows,'stats':stats,'matched_file_minus_dgram_median_ms':statistics.median(diffs)}
    pathlib.Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)); print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
if __name__=='__main__': main()
