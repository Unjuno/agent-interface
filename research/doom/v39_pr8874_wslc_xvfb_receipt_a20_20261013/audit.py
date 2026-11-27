from pathlib import Path
import hashlib,json,importlib.util
root=Path(__file__).resolve().parent
rawp=root/'results/a20-01/raw.json'
raw=json.loads(rawp.read_text())
manifest=json.loads((root/'SOURCE_MANIFEST.json').read_text())
checks=[]
for item in manifest['files']:
 b=(root/'INPUT'/item['path']).read_bytes()
 checks.append({'path':item['path'],'expected':item['sha256'],'actual':hashlib.sha256(b).hexdigest(),'ok':len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']})
spec=importlib.util.spec_from_file_location('analyzer',root/'INPUT/research/doom/analyze_map01_direct_retained_input_v2.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
recomputed=mod.analyze([raw['admission'],raw['release_transition']])
owner=raw['release_transition']; receipt=owner.get('owner_thread_keyup_receipt') or {}
receipt_ok=(owner.get('owner_thread_keyup_verified') is True and owner.get('owner_thread_keyup_receipt_count')==1 and receipt.get('event')=='owner_explicit_keyup' and receipt.get('owner_id')==owner.get('owner_id') and receipt.get('intent_token')==owner.get('intent_token') and receipt.get('server_sync_completed') is True and receipt.get('physical_verification_authoritative') is False and owner['release_call_started_ns']<=receipt['owner_keyrelease_started_ns']<=receipt['owner_sync_returned_ns']<=owner['release_call_returned_ns'])
checks_event=(len(raw['client_events'])==2 and [x['type'] for x in raw['client_events']]==[2,3] and all(x['window']==raw['client_window'] and x['detail']==raw['keycode'] for x in raw['client_events']))
cleanup=raw['owner_cleanup']
result={'experiment_id':'v39_pr8874_wslc_xvfb_receipt_a20_20261013','source_sha_checks':checks,'raw_sha256':hashlib.sha256(rawp.read_bytes()).hexdigest(),'external_x11_event_pair_ok':checks_event,'keymap_while_held':raw['keymap'].get('while_held'),'keymap_after_up':raw['keymap'].get('after_explicit_up'),'v4_owner_up_receipt_ok':receipt_ok,'close_empty_verified':any(x.get('event')=='owner_release' and x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in cleanup['records']),'owner_closed_stopped_thread_dead':cleanup['closed'] and cleanup['stopped'] and not cleanup['thread_alive'],'xvfb_exit':raw['xvfb'].get('exit'),'analyzer_raw':raw['analyzer'],'analyzer_recomputed':recomputed,'analyzer_consistent':raw['analyzer']==recomputed,'admission_missing_owner_id':'owner_id' not in raw['admission'],'release_owner_transition_verified':owner.get('owner_transition_verified'),'container_exit':int((root/'results/a20-01/container.exit').read_text().strip()),'decision':'FAIL_ANALYZER_BRIDGE' if receipt_ok and checks_event and raw['keymap']=={'after_explicit_up':False,'while_held':True} and not recomputed['measurement_ready'] and all(c['ok'] for c in checks) else 'STOP_AUDIT'}
(root/'results/a20-01/audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
