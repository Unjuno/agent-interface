import argparse,copy,json
from pathlib import Path
FLAGS=('focus_drift','modal_transition','geometry_drift','window_replacement')
EXPECTED={'focus':'450276c3a000f69aba80270472d735306a2c0c4d','modal':'867212574da214672d645689d91d59e4d1641523','ghd':'fe0065b195f97da8ae943a55f59504688a886d91','research':'a433f970e71b04949a1235a3526cb10ca93a152f','roadmap':'258b42f9279aeb1ef52e96783479b85f0d89f4eb'}
def derive(L,S):
    rows=L['rows'];cov={f:sum(r.get(f) is True for r in rows) for f in FLAGS};apps=sorted(set(a for r in rows for a in r['apps']))
    integrated=[r['id'] for r in rows if r.get('same_session_all_four') is True and all(r.get(f) is True for f in FLAGS)]
    exact=all(S['sources'][k]['git_blob']==v for k,v in EXPECTED.items())
    good=all(cov[f]>0 for f in FLAGS) and len(apps)>=2 and not integrated and L['research_status']['longer_mixed_app_sessions_listed_as_future'] is True and exact and all(r['same_session_all_four'] is False for r in rows)
    return cov,apps,integrated,exact,good
def valid(R,L,S):
    cov,apps,integ,exact,good=derive(L,S)
    return good and R.get('decision')=='PASS_RETAINED_MULTI_APP_COMPONENTS_NOT_INTEGRATED_SCOPED' and R.get('coverage')==cov and R.get('apps')==apps and R.get('integrated_all_four_rows')==integ and R.get('source_map_exact')==exact and (R.get('formal_invocations'),R.get('reruns'),R.get('replacements'),R.get('tuning'))==(1,0,0,0)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ledger',required=True);ap.add_argument('--source-map',required=True);ap.add_argument('--result',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    L=json.loads(Path(a.ledger).read_text());S=json.loads(Path(a.source_map).read_text());R=json.loads(Path(a.result).read_text());errors=[]
    if not valid(R,L,S): errors.append('primary')
    controls={}
    for name,mut in {
      'erase_focus':lambda l,s,r:l['rows'][0].__setitem__('focus_drift',False),
      'forge_integrated':lambda l,s,r:l['rows'][2].update({'focus_drift':True,'modal_transition':True,'same_session_all_four':True}),
      'source_blob':lambda l,s,r:s['sources']['focus'].__setitem__('git_blob','0'*40),
      'future_closed':lambda l,s,r:l['research_status'].__setitem__('longer_mixed_app_sessions_listed_as_future',False),
      'invocation':lambda l,s,r:r.__setitem__('formal_invocations',2),
      'decision':lambda l,s,r:r.__setitem__('decision','FAIL')
    }.items():
        l=copy.deepcopy(L);s=copy.deepcopy(S);r=copy.deepcopy(R);mut(l,s,r);controls[name]=not valid(r,l,s)
    if not all(controls.values()): errors.append('corruption')
    out={'pass':not errors,'errors':errors,'corruption_controls':controls,'derived':{'coverage':derive(L,S)[0],'apps':derive(L,S)[1],'integrated_all_four_rows':derive(L,S)[2]}}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__':main()
