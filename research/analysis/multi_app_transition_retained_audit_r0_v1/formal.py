import argparse,hashlib,json
from pathlib import Path

FLAGS=('focus_drift','modal_transition','geometry_drift','window_replacement')
EXPECTED_BLOBS={
 'focus':'450276c3a000f69aba80270472d735306a2c0c4d',
 'modal':'867212574da214672d645689d91d59e4d1641523',
 'ghd':'fe0065b195f97da8ae943a55f59504688a886d91',
 'research':'a433f970e71b04949a1235a3526cb10ca93a152f',
 'roadmap':'258b42f9279aeb1ef52e96783479b85f0d89f4eb'
}
def analyze(ledger,smap):
    rows=ledger['rows']
    coverage={f:sum(bool(r.get(f)) for r in rows) for f in FLAGS}
    apps=sorted({a for r in rows for a in r.get('apps',[])})
    integrated=[r['id'] for r in rows if all(r.get(f) is True for f in FLAGS) and r.get('same_session_all_four') is True]
    source_exact=all(smap['sources'][k]['git_blob']==v for k,v in EXPECTED_BLOBS.items())
    research_future=ledger['research_status'].get('longer_mixed_app_sessions_listed_as_future') is True
    no_launder=all(r.get('same_session_all_four') is False for r in rows)
    good=all(coverage[f]>0 for f in FLAGS) and len(apps)>=2 and integrated==[] and source_exact and research_future and no_launder
    return {
      'decision':'PASS_RETAINED_MULTI_APP_COMPONENTS_NOT_INTEGRATED_SCOPED' if good else 'FAIL_INTEGRITY',
      'coverage':coverage,'apps':apps,'integrated_all_four_rows':integrated,
      'source_map_exact':source_exact,'research_future_open':research_future,
      'component_rows':len(rows),'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0
    }
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ledger',required=True);ap.add_argument('--source-map',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    L=json.loads(Path(a.ledger).read_text());S=json.loads(Path(a.source_map).read_text());r=analyze(L,S)
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest()
    Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
