from pathlib import Path
import json,math
root=Path(__file__).resolve().parent/'sample-pair-03';cell=root/'00-coast'
r=json.loads((cell/'RESULT.json').read_text());events=[json.loads(x) for x in (cell/'events.jsonl').read_text().splitlines()];rows=[json.loads(x) for x in (cell/'scorer-last-action.jsonl').read_text().splitlines()]
selected=[x for x in rows if x['coherent_tic'] and r['window_start_ns']<=x['sample_started_ns'] and x['sample_returned_ns']<=r['window_end_ns']]
initial=next(e for e in events if e.get('event')=='typed_observation' and e.get('id')=='initial')
nearest=min((x for x in rows if x['coherent_tic']),key=lambda x:abs(x['sample_returned_ns']-initial['capture_ns']))
agreement={k:{'HUD':initial['signals'][k],'API':nearest['variables'][v]} for k,v in [('health','HEALTH'),('ammo','AMMO1')]}
finite=bool(selected) and all(math.isfinite(v) for x in selected for v in x['variables'].values())
matches=all(x['HUD']['status']=='observed' and x['HUD']['value']==x['API'] for x in agreement.values())
health=[x['variables']['HEALTH'] for x in selected];changed=bool(health) and min(health)<max(health)
result={'disposition':'PASS_SAMPLED_DAMAGE_EXPOSURE_SCOPED' if finite and matches and changed else 'FAIL_OR_HOLD_MEASUREMENT_QUALIFICATION','samples':len(selected),'health_min':min(health) if health else None,'health_max':max(health) if health else None,'first':selected[0] if selected else None,'last':selected[-1] if selected else None,'all_action_neutral':all(not any(x['action']) for x in selected),'initial_agreement':agreement,'initial_API_offset_ns':nearest['sample_returned_ns']-initial['capture_ns'],'final':json.loads((cell/'FINAL.json').read_text()),'limits':'Post-result authored inspection; nearest API/HUD is cross-clock proximity not same-state proof. Sampled damage exposure not cause/useful recovery benefit. Independent review pending.'}
(root/'SAVED_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
