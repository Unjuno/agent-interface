from cache import monitor
from oracle import decide,effect

def evaluate_trace(entry,rows):
    reference_calls=0; candidate_semantic_calls=1
    mismatches=stale=missed=unnecessary=authority=wrong_effect=0
    reuse=ambiguous=0; invalidated=False; candidate_effect=reference_effect=0
    for ev in rows:
        ref=decide(entry,ev); reference_calls+=1
        cand=monitor(entry,ev) if not invalidated else {'disposition':'YIELD','action':None,'reason':'cache_invalidated','grants_input_authority':False}
        if cand['disposition']=='YIELD': invalidated=True
        mismatches += int((cand['disposition'],cand.get('action'))!=(ref['disposition'],ref.get('action')))
        stale += int(cand['disposition']=='KEEP' and ref['disposition']=='YIELD')
        missed += int(ev.regime=='HARD_INVALIDATION' and cand['disposition']!='YIELD')
        unnecessary += int(cand['disposition']=='YIELD' and ref['disposition']=='KEEP')
        authority += int(cand.get('grants_input_authority') is not False)
        ce=effect(entry,ev,cand); re=effect(entry,ev,ref)
        wrong_effect += int(ce['effect']=='WRONG_EFFECT')
        candidate_effect += ce['delta']; reference_effect += re['delta']
        reuse += int(cand['disposition']=='KEEP')
        ambiguous += int(ev.regime=='AMBIGUOUS_BOUNDARY')
    return {'reference_semantic_calls':reference_calls,'candidate_semantic_calls':candidate_semantic_calls,'mismatches':mismatches,'stale_continuation_attempts':stale,'missed_hard_invalidations':missed,'unnecessary_yields':unnecessary,'authority_errors':authority,'wrong_effects':wrong_effect,'candidate_effect':candidate_effect,'reference_effect':reference_effect,'reuse_cycles':reuse,'ambiguous_cases':ambiguous}
