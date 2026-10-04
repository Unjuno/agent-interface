import hashlib, json, pathlib, sys
root=pathlib.Path('/out')
raw=json.loads((root/'raw.json').read_text())
assert raw['inputs_submitted']==[]
assert [r['phase'] for r in raw['rows']]==['initial','coast']
a,b=raw['rows']
assert a['tic_before']==a['tic_after']==1
assert b['tic_before']==1 and b['tic_after']==36
for row in raw['rows']:
    assert row['direct']==row['state_game_variables'], row['phase']
    assert len([row['direct'][f'AMMO{i}'] for i in range(10)])==10
    assert hashlib.sha256((root/row['png']).read_bytes()).hexdigest()==row['png_sha256']
assert a['direct']['SELECTED_WEAPON_AMMO']==50
assert a['direct']['AMMO1']==0
assert a['direct']['SELECTED_WEAPON']==2
assert a['direct']['AMMO2']==50 and a['direct']['AMMO4']==50
assert a['direct']['HEALTH']==b['direct']['HEALTH']==100
result={
 'schema':'selected-ammo-signal-audit-v1',
 'run_id':raw['run_id'],
 'disposition':'PARTIAL_SIGNAL_SEMANTICS_PASS_SLOT_MAPPING_HOLD',
 'checks':{'no_inputs':True,'tic_bracketed':True,'direct_equals_game_state':True,'all_ammo_slots_retained':True,'selected_ammo_50':True,'ammo1_0':True,'health_stable_100':True,'png_hashes_match':True},
 'interpretation':'AMMO1 is not selected-weapon ammunition in this sampled state: SELECTED_WEAPON=2, SELECTED_WEAPON_AMMO=50, AMMO1=0. HUD shows 50. AMMO2 and AMMO4 are both 50, so this one state cannot establish a unique weapon-index-to-ammo-slot mapping.',
 'scope_limits':['single fresh initial episode','no task action or model','no damage or recovery effect','two samples only','HUD values manually read from retained screenshots','not a useful-feedback-onset measurement']}
(root/'AUDIT.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
