from __future__ import annotations

def _tiles(values):
    try: s=set(values)
    except TypeError as exc: raise ValueError('oracle_bad_tile_set') from exc
    if any((not isinstance(v,int)) or v<0 or v>=64 for v in s): raise ValueError('oracle_bad_tile')
    return s

def reduce_history(scope:str, ops:list[dict]):
    generation=1; initialized=False; current=set(); receipts={}; suppressions=0; forwards=0; rows=[]
    for op in ops:
        kind=op['kind']
        try:
            if kind=='INSTALL':
                rid=op['receipt_id']; rel=_tiles(op['relevant_tiles'])
                if not isinstance(rid,str) or not rid: raise ValueError('oracle_bad_receipt')
                if not initialized:
                    current=set(rel); initialized=True
                elif rel != current: raise ValueError('oracle_install_not_current')
                rec={'receipt_id':rid,'scope':scope,'generation':generation,'relevant_tiles':sorted(rel)}
                if rid in receipts:
                    if receipts[rid] != rec: raise ValueError('oracle_conflicting_receipt')
                    res={'result':'DUPLICATE_NOOP','generation':generation}
                else:
                    receipts[rid]=rec; res={'result':'INSTALLED','generation':generation}
                rows.append({'kind':kind,'ok':True,'result':res})
            elif kind=='ADVANCE':
                if not initialized: raise ValueError('oracle_advance_before_init')
                rel=_tiles(op['relevant_tiles'])
                if rel==current:
                    res={'result':'NOOP_SAME_RELEVANCE','generation':generation}
                else:
                    generation+=1; current=set(rel); res={'result':'ADVANCED','generation':generation}
                rows.append({'kind':kind,'ok':True,'result':res})
            elif kind=='GATE':
                changed=_tiles(op['changed_tiles']); critical=_tiles(op['critical_tiles']); rid=op['receipt_id']
                if not isinstance(rid,str) or not rid: raise ValueError('oracle_bad_gate_receipt')
                rec=receipts.get(rid); action='FORWARD_FULL_CURRENT'; reason='MISSING_RECEIPT'
                if rec is not None:
                    claimed_scope=op.get('claimed_scope',rec['scope']); claimed_generation=op.get('claimed_generation',rec['generation'])
                    if claimed_scope != scope or claimed_scope != rec['scope']:
                        reason='WRONG_SCOPE_RECEIPT'
                    elif not isinstance(claimed_generation,int) or claimed_generation<1 or claimed_generation!=rec['generation']:
                        reason='RECEIPT_IDENTITY_MISMATCH'
                    elif rec['generation'] != generation:
                        reason='STALE_RELEVANCE_GENERATION'
                    elif changed & critical:
                        reason='CRITICAL_CHANGE'
                    elif changed & current:
                        reason='CURRENT_RELEVANT_CHANGE'
                    else:
                        action='SUPPRESS_EXACT_IRRELEVANT'; reason='CURRENT_IRRELEVANT_CHANGE'
                if action.startswith('SUPPRESS'): suppressions+=1
                else: forwards+=1
                rows.append({'kind':kind,'ok':True,'result':{'action':action,'reason':reason,'generation':generation}})
            else:
                raise ValueError('oracle_bad_kind')
        except ValueError as exc:
            rows.append({'kind':kind,'ok':False,'error':str(exc)})
    return {'rows':rows,'state':{'scope':scope,'generation':generation,'initialized':initialized,'current_relevant':sorted(current),'receipts':{k:receipts[k] for k in sorted(receipts)},'suppressions':suppressions,'forwards':forwards}}
