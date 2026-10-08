from cache import CacheEntry,Evidence,validate_entry,validate_evidence

# Independent semantic reference: explicit truth table, not cache.monitor.
def decide(entry,evidence):
    e=validate_entry(entry); v=validate_evidence(evidence)
    bad=(
      v.intent_id!=e.intent_id or v.strategy_id!=e.strategy_id or
      v.generation!=e.generation or v.provenance!=e.provenance or
      v.age>e.max_age or v.update_index>=e.max_updates or
      v.regime in ('HARD_INVALIDATION','AMBIGUOUS_BOUNDARY')
    )
    if bad:
        return {'disposition':'YIELD','action':None,'grants_input_authority':False}
    return {'disposition':'KEEP','action':e.allowed_action,'grants_input_authority':False}


def effect(entry,evidence,decision):
    truth=decide(entry,evidence)
    if decision['disposition']=='KEEP':
        if truth['disposition']!='KEEP' or decision.get('action')!=entry.allowed_action:
            return {'effect':'WRONG_EFFECT','delta':-1}
        return {'effect':'USEFUL_PROGRESS','delta':1}
    return {'effect':'NO_TASK_INPUT','delta':0}
