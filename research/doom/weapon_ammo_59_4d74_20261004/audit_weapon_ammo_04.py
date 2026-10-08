from pathlib import Path
import json,math
root=Path(__file__).resolve().parent/'sample-pair-04';cell=root/'00-coast'
r=json.loads((cell/'RESULT.json').read_text());events=[json.loads(x) for x in (cell/'events.jsonl').read_text().splitlines()];rows=[json.loads(x) for x in (cell/'scorer-last-action.jsonl').read_text().splitlines()]
selected=[x for x in rows if x['coherent_tic'] and r['window_start_ns']<=x['sample_started_ns'] and x['sample_returned_ns']<=r['window_end_ns']]
initial=next(e for e in events if e.get('event')=='typed_observation' and e.get('id')=='initial')
near=min(rows,key=lambda x:abs(x['sample_returned_ns']-initial['capture_ns']))
signals={'health':near['variables']['HEALTH'],'ammo':near['variables']['SELECTED_WEAPON_AMMO']}
agreement={k:{'HUD':initial['signals'][k]['value'],'API':v,'difference':v-initial['signals'][k]['value']} for k,v in signals.items()}
slot=near['variables'].get(f"AMMO{int(near['variables']['SELECTED_WEAPON'])%10}")
finite=bool(selected) and all(math.isfinite(v) for x in selected for v in x['variables'].values())
ok=finite and all(abs(x['difference'])<1e-6 for x in agreement.values()) and abs(slot-near['variables']['SELECTED_WEAPON_AMMO'])<1e-6
audit={'disposition':'PASS_HUD_WEAPON_AMMO_BINDING_SCOPED' if ok else 'FAIL_OR_HOLD_BINDING','sample_count':len(selected),'all_neutral':all(not any(x['action']) for x in selected),'selected_weapon':near['variables']['SELECTED_WEAPON'],'selected_weapon_ammo':near['variables']['SELECTED_WEAPON_AMMO'],'matching_slot_ammo':slot,'initial_hud_comparison':agreement,'nearest_api_offset_ns':near['sample_returned_ns']-initial['capture_ns'],'health_window_min':min(x['variables']['HEALTH'] for x in selected),'health_window_max':max(x['variables']['HEALTH'] for x in selected),'final_score':r['score'],'child_exit':r['child_exit'],'reader_alive':r['reader_alive'],'external_rescue':json.loads((cell/'FINAL.json').read_text())['external_rescue'],'limits':'Post-result saved authored audit; nearest HUD/API are not simultaneous. Component identity and finite samples only; no damage exposure or recovery efficacy.'}
(root/'SAVED_AUDIT.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
