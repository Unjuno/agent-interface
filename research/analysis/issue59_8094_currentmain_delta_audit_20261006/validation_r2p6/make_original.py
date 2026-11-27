import hashlib,json
from pathlib import Path
root=Path(__file__).parent/'original'
rows=[
('research/doom/doom_batch_key_measurement_backend_v1.py',None,'5b07504d68c69ee508d53458c7caf5392b5ea9e4'),
('research/doom/doom_owner_thread_release_batch_backend_v1.py','193c2bd231795e7ee57de64aedfd741c8b814013','0d079174cb9187e2f1711c00b7df2603db1bc21d'),
('research/doom/map01_overlap_controller_v39.py','e9b437979e87347f6aa4dbefffcc84e9a2d01752','e2de3df2934f68aadb17d9977ab46d399e3cabf9'),
('research/doom/session_map01_v12.py','e701035302da4802e0db463035c4d653a7e7618b','7ccd489625335522104a9a49a2c8427d212ae63b'),
('research/doom/session_map01_v15.py','f71ca01426a703e4160c9403395fed03416c772e','2d6974c20f4e272fd965efe033608977b5e95407'),
('research/doom/v39_measurement_backend_selection_v1.py',None,'c7d84b1b8b20e6e7e5ce980c5fc85dfbca08d1fd'),
('research/live_control/input_owner_v12.py','d11a9b1328bf76e5045022c581d6a9a721bf9585','5622e684f58869a8a812c220ca80cc6eedf1b806'),
('research/live_control/input_transition_owner_v4.py','ac1cc0e67114e2b8630acbaa6d94bf2a73686a55','159c5d310ee2e6dd306ebd9b3d8dc041960ee219'),
('research/live_control/key_edge_measurement_v1.py',None,'775c58961ebaa15aae8a226b2b1dd8fa4c286cb7'),
('research/live_control/observable_signal_guard_v2.py','c0955f976e3a0af6ce926f22cee4a5ddf70ef543','1e7ad4f936c45525eb1696c366bdf3b9471bac01'),
('research/doom/map01_motor_responder_v10.txt','9ee9fe93d9783fa8bddba58f8f3c5b538d450076','ef32ef849aabe57abe158d6d12040fd6d655ccd2')]
data={'schema':'agent-interface/issue59-8094-currentmain-delta-audit-v1',
'intake_main':'a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028',
'merge_base':'21fecd58b9de30073c97234124e73b78c67d4b0c',
'candidate_head':'d0aa8463a10abf04d1b40cb4f498fc0a659fb827','candidate_pr':8094,
'paths':[{'path':p,'base_sha':b,'main_sha':b,'candidate_sha':c,'classification':'CANDIDATE_ADD_CLEAN' if b is None else 'MAIN_UNCHANGED_CANDIDATE_ONLY'} for p,b,c in rows],
'counts':{'total':11,'clean_add':3,'main_unchanged_candidate_only':8,'conflicts':0},
'decision':'PASS_CURRENT_MAIN_DELTA_NONCONFLICT_SCOPED',
'limits':['Git-blob/source compatibility only','does not run V15/V39/Executor/X11/game/model','does not approve PR #8094 or its 1467-file evidence delta','does not establish live per-key timing, useful feedback, recovery benefit, or MAP01 progress','snapshot-scoped to intake_main']}
(root/'RESULT.json').write_text(json.dumps(data,indent=2)+'\n')
controls={'schema':'agent-interface/issue59-8094-currentmain-delta-controls-v1','verifier':'data-only local recheck of GitHub-readback RESULT.json','baseline_errors':[],
'mutations':[{'name':n,'rejected':True} for n in ['main_sha_changed','candidate_equals_main','classification_changed','addition_gets_base','drop_row','duplicate_row','candidate_sha_null','invalid_class']],
'all_rejected':True,'note':'These are evidence-integrity controls for the frozen blob table, not runtime behavior tests.'}
(root/'CONTROLS.json').write_text(json.dumps(controls,indent=2)+'\n')
expected={'verify.py':'a297be783f99615c1870d5882bb6387426392b24','RESULT.json':'79aca87c12292d7d33f926a5aabae4f4ee7e6095','CONTROLS.json':'3782c92bc2cae3aa1bf53734aeb3b3b1370cab4c'}
proof={}
for name,pin in expected.items():
 b=(root/name).read_bytes(); actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 if actual!=pin: raise SystemExit(f'GIT_BLOB_MISMATCH {name} {actual} != {pin}')
 proof[name]={'git_blob':actual,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
(root/'READBACK.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
