import json,sys
orig=json.load(open(sys.argv[1])); cand=json.load(open(sys.argv[2])); expected={
 'terminal_opt_in':True,'terminal_default_isolated':True,
 'stale_accept_cannot_satisfy_submit':True,'stale_reject_cannot_satisfy_submit':True,
 'duplicate_terminal_rejected':True,'wrong_terminal_id_rejected':True,
 'queued_fallback_accepted':True,'stale_then_queued_fallback_accepted':True}
oe=[k for k,v in orig.items() if not v]; ce=[k for k,v in cand.items() if not v]
errors=[]
if oe != ['terminal_default_isolated','terminal_opt_in']: errors.append('original witness set mismatch:'+repr(oe))
if ce: errors.append('candidate failures:'+repr(ce))
if set(cand)!=set(expected): errors.append('candidate case set mismatch')
print(json.dumps({'decision':'PASS_REPLAY_SCOPE_CANDIDATE_SCOPED' if not errors else 'HOLD_MATRIX_AUDIT','original_expected_failures':oe,'candidate_failures':ce,'cases':len(expected),'errors':errors},sort_keys=True))
sys.exit(bool(errors))
