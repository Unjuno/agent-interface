import hashlib,json,pathlib,sys
p=pathlib.Path(__file__).resolve().parent
rawp=pathlib.Path(sys.argv[1]); raw=json.loads(rawp.read_text()); t=raw.get('terminal') or {}; rel=t.get('release') or {}
checks={'candidate_complete':raw.get('status')=='CANDIDATE_COMPLETE','alias_codes_equal_nonzero':len(raw.get('alias_codes',[]))==2 and raw['alias_codes'][0]!=0 and raw['alias_codes'][0]==raw['alias_codes'][1],'terminal_failed':t.get('status')=='failed','terminal_release_verified':rel.get('verified') is True,'keymap_neutral_after_cleanup':raw.get('keymap_after') is False,'xvfb_exited':raw.get('xvfb_exit')==0,'no_cleanup_errors':not raw.get('cleanup_errors')}
res={'schema':'issue59-a09-independent-audit-v1','outcome':'PASS_METHOD_SCOPED' if all(checks.values()) else ('STOP' if raw.get('status')=='STOP' else 'FAIL'),'checks':checks,'raw_sha256':hashlib.sha256(rawp.read_bytes()).hexdigest()}
(p/'results/A09_AUDIT.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n'); print(json.dumps(res,sort_keys=True))
