from __future__ import annotations
import json,sys
from pathlib import Path
rows=[json.loads(x) for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()]
expected=['get_episode_time','is_episode_finished','is_player_dead','get_game_variable','get_game_variable','get_ticrate','is_episode_timeout_reached','get_episode_time']
errors=[]; reports=[]
for r in rows:
    pre=r.get('pre_passive_reads',[]); post=r.get('post_passive_reads',[]); ev=r.get('scorer_getters',[])
    vals=[x.get('value') for x in ev]
    result=r.get('scorer_return',{})
    pre_span=pre[-1]['end_ns']-pre[0]['start_ns'] if pre else 0
    post_span=post[-1]['end_ns']-post[0]['start_ns'] if post else 0
    scorer_bounds=bool(ev) and r.get('scorer_start_ns',0)<=ev[0]['start_ns']<=ev[-1]['end_ns']<=r.get('scorer_end_ns',0)
    getter_order_time=all(a['end_ns']<=b['start_ns'] for a,b in zip(ev,ev[1:]))
    returned_sample_in_bounds=r.get('scorer_start_ns',0)<=result.get('sample_ns',-1)<=r.get('scorer_end_ns',0)
    coherent=len(vals)==8 and vals[0]==vals[7]
    output_matches=(result.get('kill_count')==int(vals[3]) and result.get('death_count')==int(vals[4])
      and result.get('episode_finished')==bool(vals[1]) and result.get('player_dead')==bool(vals[2])
      and result.get('map_exit')==bool(vals[1] and not vals[2] and not vals[6])) if len(vals)==8 else False
    ok={'setup':r.get('setup_status')=='ok','cleanup':r.get('cleanup',{}).get('game_closed') is True,
      'scorer_returned':r.get('scorer_status')=='returned','exact_getter_order':[x.get('name') for x in ev]==expected,
      'getter_calls_all_returned':len(ev)==8 and all(x.get('status')=='ok' for x in ev),
      'coherent_tic':coherent,'scorer_bounds':scorer_bounds,'getter_timestamps_ordered':getter_order_time,
      'returned_sample_in_bounds':returned_sample_in_bounds,'scorer_output_matches_getters':output_matches,
      'passive_pre_window':len(pre)>=100 and pre_span>=1_400_000_000,
      'passive_post_window':len(post)>=25 and post_span>=400_000_000,
      'passive_api_stays_at_initial_tic':bool(pre and post) and {x['tic'] for x in pre+post}=={1},
      'no_action_calls':r.get('action_calls')==0,
      'fixture_configuration':r.get('mode')=='Mode.ASYNC_SPECTATOR' and r.get('ticrate')==35,
      'environment_hashes':r.get('engine_binary_sha256')=='a61c08bf4e30bb111241f9f6148ad32f4084080bc5150fda71db25f6271cbb8f' and r.get('scorer_sha256')=='1a6da676db9c6b2aa61ccf0f600a1565395e906736bb07a50b2006e100d7ca98' and r.get('wad_sha256')=='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'}
    for name,val in ok.items():
        if not val: errors.append({'index':r.get('index'),'check':name})
    tics=[x.get('value') for x in ev if x.get('name')=='get_episode_time']
    reports.append({'index':r.get('index'),'setup':ok['setup'],'scorer_status':r.get('scorer_status'),
      'scorer_return':r.get('scorer_return'),'scorer_tic_getters':tics,
      'pre_api_tics':sorted(set(x['tic'] for x in pre)),'post_api_tics':sorted(set(x['tic'] for x in post)),
      'pre_read_count':len(pre),'post_read_count':len(post),'pre_span_ns':pre_span,'post_span_ns':post_span,
      'getter_count':len(ev),'cleanup':ok['cleanup'],'checks':ok})
out={'schema':'issue3453-construction-clock50-audit-v1','decision':'PASS_CONSTRUCTION_ONLY_UNINSTRUMENTED_EXACT_SCORER' if len(rows)==6 and not errors else 'HOLD_OR_FAIL',
 'formal_allocation':False,'rows':len(rows),'errors':errors,'reports':reports,
 'limitations':['No independent internal uninstrumented tic trace is available; API snapshot tics are not a phase witness.',
 'One exact scorer call per fresh construction session is not the frozen 120-row allocation; no formal rows are authorized.']}
print(json.dumps(out,indent=2,sort_keys=True))
