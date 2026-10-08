from __future__ import annotations
import json,sys
from pathlib import Path
rows=[json.loads(x) for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()]
delays=[.5,2,6,10,14,20]; names=['get_episode_time','is_episode_finished','is_player_dead','get_game_variable','get_game_variable','get_ticrate','is_episode_timeout_reached','get_episode_time']; errors=[]; reports=[]
for r in rows:
    i=r.get('index'); pre=r.get('passive_reads',[]); ev=r.get('scorer_getters',[]); vals=[x.get('value') for x in ev]; result=r.get('scorer_return',{})
    span=r.get('passive_window_end_ns',0)-r.get('passive_window_start_ns',0); tics=sorted(set(x['tic'] for x in pre))
    checks={'setup':r.get('setup_status')=='ok','cleanup':r.get('cleanup',{}).get('game_closed') is True,
      'frozen_delay':i is not None and r.get('delay_s')==delays[i], 'passive_span':span>=r.get('delay_s',999)*1e9-100_000_000,
      'passive_polling':len(pre)>=max(4,int(r.get('delay_s',0)*5)), 'no_action_calls':r.get('action_calls')==0,
      'fixture':r.get('mode')=='Mode.ASYNC_SPECTATOR' and r.get('ticrate')==35,
      'hashes':r.get('engine_binary_sha256')=='a61c08bf4e30bb111241f9f6148ad32f4084080bc5150fda71db25f6271cbb8f' and r.get('scorer_sha256')=='1a6da676db9c6b2aa61ccf0f600a1565395e906736bb07a50b2006e100d7ca98' and r.get('wad_sha256')=='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b',
      'scorer_returned':r.get('scorer_status')=='returned','getter_order':[x.get('name') for x in ev]==names,
      'getter_tics_coherent':len(vals)==8 and vals[0]==vals[7],
      'getter_values_complete':len(ev)==8 and all(x.get('status')=='ok' for x in ev),
      'return_reconstructed':len(vals)==8 and result.get('kill_count')==int(vals[3]) and result.get('death_count')==int(vals[4]) and result.get('episode_finished')==bool(vals[1]) and result.get('player_dead')==bool(vals[2]) and result.get('map_exit')==bool(vals[1] and not vals[2] and not vals[6]),
      'final_read_present':r.get('final_tic') is not None and isinstance(r.get('final_finished'),bool)}
    for k,v in checks.items():
        if not v: errors.append({'index':i,'check':k})
    reports.append({'index':i,'delay_s':r.get('delay_s'),'passive_read_count':len(pre),'api_tics':tics,
      'finished_values':sorted(set(x['finished'] for x in pre)),'final_tic':r.get('final_tic'),'final_finished':r.get('final_finished'),
      'scorer_tic_getters':[vals[0],vals[7]] if len(vals)==8 else vals,'scorer_return':result,'checks':checks})
if {r.get('index') for r in rows}!={0,1,2,3,4,5}:
    errors.append({'check':'frozen_six_cell_coverage'})
out={'schema':'issue3453-construction-clock52-audit-v1','decision':'PASS_CONSTRUCTION_ONLY_UNINSTRUMENTED_SCORER_TIMECOURSE' if len(rows)==6 and not errors else 'HOLD_OR_FAIL',
 'formal_allocation':False,'rows':len(rows),'errors':errors,'reports':reports,
 'limitations':['No independent engine tic-edge trace; API tic changes are not a direct engine-clock witness or phase measurement.',
 'Six duration cells are construction-only and do not estimate the frozen phase/load schedule or formal failure probability.']}
print(json.dumps(out,indent=2,sort_keys=True))
