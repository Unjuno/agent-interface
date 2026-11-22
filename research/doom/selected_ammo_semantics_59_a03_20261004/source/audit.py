import hashlib, json, pathlib
from PIL import Image
root=pathlib.Path('/out')
raw=json.loads((root/'raw.json').read_text())
assert raw['run_id']=='59-selected-ammo-semantics-a03-20261004'
assert raw['inputs_submitted']==[]
assert raw['wad_sha256']=='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
assert len(raw['rows'])==2
for i,row in enumerate(raw['rows']):
    assert row['phase']==('initial' if i==0 else 'coast')
    assert row['screen_size']==[640,480]
    assert row['episode_tic_before_state']==row['episode_tic_after_state']==row['episode_tic_before_direct_reads']==row['episode_tic_after_direct_reads']
    assert row['direct']==row['state_game_variables']
    assert row['direct']['HEALTH']==100.0
    assert row['direct']['SELECTED_WEAPON_AMMO']==50.0
    assert row['direct']['AMMO1']==0.0
    assert row['binding_metadata_note']=='synthetic in-memory binding metadata; this is not a live X11 pointer/focus identity'
    image=root/row['frame_png']
    assert hashlib.sha256(image.read_bytes()).hexdigest()==row['frame_sha256']
    with Image.open(image) as frame: assert frame.size==(640,480)
    assert row['signals']['health']['status']=='observed' and row['signals']['health']['value']==100
    assert row['signals']['ammo']['status']=='observed' and row['signals']['ammo']['value']==50
    assert row['signals']['health']['sequence']==row['signals']['ammo']['sequence']==i
    assert row['signals']['health']['capture_ns']==row['signals']['ammo']['capture_ns']
    assert row['signals']['health']['wad_sha256']==raw['wad_sha256']
    assert row['signals']['ammo']['wad_sha256']==raw['wad_sha256']
result={'schema':'selected-ammo-hud-reader-audit-v1','run_id':raw['run_id'],'disposition':'PASS_HASHED_WAD_GLYPH_READER_AND_SAME_TIC_API_SCOPED','checks':{'fresh_wad_hash_matches_reader':True,'no_inputs_submitted':True,'two_same_tic_samples':True,'api_values_equal_game_state_vector':True,'health_reader_matches_api_and_hud':True,'ammo_reader_matches_selected_weapon_ammo_and_hud':True,'AMMO1_retained_separately_as_zero':True,'all_frames_640x480_and_hash_bound':True,'same_frame_capture_metadata_for_both_signals':True},'interpretation':'At both retained tics, current-main v3 WAD-glyph HUD reader returns health=100 and ammo=50 from the exact in-memory 640x480 frame. Same-tic direct API and GameState values match; SELECTED_WEAPON_AMMO=50 while AMMO1=0. The coast frame visibly has a close enemy and health remains 100. The result disambiguates the selected-ammo signal but does not identify unique AMMO slot mapping.', 'scope_limits':['two observations in one fresh episode','input-free 35-tic coast only','synthetic in-memory focus/surface binding metadata','no actual X11 window identity or focus check','no model/controller delivery','no damage or useful task progress','no per-key timing, threat reaction, or bounded recovery']}
(root/'AUDIT.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
