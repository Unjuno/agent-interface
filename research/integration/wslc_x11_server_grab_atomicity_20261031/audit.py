import json,sys
from pathlib import Path
b=Path(sys.argv[1]);rs={}
for n in ('a01','a02','a03','a04','a05'):
 p=b/('wslc-x11-server-grab-20261031-'+n);assert (p/'container.exit').read_text().strip()=='0';rs[n]=json.loads((p/'output/result.json').read_text())
a=rs['a01'];assert a['before']==a['inside_grab']==a['target'] and a['after_ungrab']==a['overlay'];assert [e['type'] for e in a['target_events']]==[4,5] and all(e['window']==a['target'] and e['detail']==1 for e in a['target_events']) and a['overlay_events']==[] and a['buttons']==0;assert a['grab_acquired_ns']<=a['map_request_queued_ns']<=a['pair_completed_ns']<=a['ungrab_completed_ns']
c=rs['a02'];assert c['holder_confirmed_grab'] and c['probe_blocked_before_kill'] and c['holder_exit']==-9 and c['probe_exit']==0 and c['probe_stdout']=='RESPONSIVE'
for n in ('a03','a04'):
 r=rs[n];assert r['before']==r['target'] and r.get('after_map',r.get('inside_grab'))==r['overlay'] and r['target_events']==[] and [e['type'] for e in r['overlay_events']]==[4,5] and all(e['window']==r['overlay'] and e['detail']==1 for e in r['overlay_events']) and r['buttons']==0
h=rs['a05'];assert h['holder_confirmed_grab_and_down'] and h['probe_blocked_before_kill'] and h['holder_exit']==-9 and h['probe_exit']==0 and h['probe_stdout']=='RESPONSIVE' and h['button_down_after_kill'] is True and h['button_down_after_external_release'] is False
print(json.dumps({'held_button_persisted_after_kill_and_external_release_cleared':True,'grab_pair_to_target':True,'queued_overlay_mapped_after_ungrab':True,'no_grab_control_pair_to_overlay':True,'held_server_blocks_probe':True,'probe_resumes_after_holder_kill':True,'grab_held_ns':a['held_ns'],'probe_post_kill_ns':c['post_kill_wait_ns']},indent=2))
