from cache import monitor
from generator import entry,valid_evidence,terminal_evidence
cs=[];e=entry(4)
def expect_yield(name,v): cs.append({'name':name,'rejected':monitor(e,v)['disposition']=='YIELD'})
for kind in ('HARD_INVALIDATION','AMBIGUOUS_BOUNDARY','GENERATION_MISMATCH','PROVENANCE_MISMATCH','EXPIRED','INTENT_MISMATCH','STRATEGY_MISMATCH','MAX_UPDATES'):
    expect_yield(kind.lower(),terminal_evidence(e,2,kind))
# Valid continuation must not be over-invalidated.
cs.append({'name':'valid_continuation_preserved','rejected':monitor(e,valid_evidence(e,2))['disposition']=='KEEP'})
# Monitor never emits authority.
cs.append({'name':'authority_never_granted','rejected':monitor(e,valid_evidence(e,1))['grants_input_authority'] is False})
assert all(x['rejected'] for x in cs);print('CORRUPTION_PASS',len(cs))
