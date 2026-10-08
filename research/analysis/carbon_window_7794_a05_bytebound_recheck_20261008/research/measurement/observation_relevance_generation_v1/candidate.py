from __future__ import annotations
from dataclasses import dataclass, asdict

VALID_TILES=frozenset(range(64))

def norm_tiles(values):
    try:
        s=frozenset(values)
    except TypeError as exc:
        raise ValueError('bad_tile_set') from exc
    if any((not isinstance(v,int)) or v not in VALID_TILES for v in s):
        raise ValueError('bad_tile_id')
    return s

@dataclass(frozen=True)
class Receipt:
    receipt_id:str
    scope:str
    generation:int
    relevant_tiles:frozenset[int]

class RelevanceGate:
    def __init__(self, scope:str):
        if not isinstance(scope,str) or not scope:
            raise ValueError('bad_scope')
        self.scope=scope
        self.generation=1
        self.initialized=False
        self.current_relevant=frozenset()
        self.receipts:dict[str,Receipt]={}
        self.suppressions=0
        self.forwards=0

    def install_relevance(self, receipt_id:str, relevant_tiles):
        if not isinstance(receipt_id,str) or not receipt_id:
            raise ValueError('bad_receipt_id')
        rel=norm_tiles(relevant_tiles)
        if not self.initialized:
            self.current_relevant=rel
            self.initialized=True
        elif rel != self.current_relevant:
            raise ValueError('install_not_current_relevance')
        rec=Receipt(receipt_id,self.scope,self.generation,rel)
        prior=self.receipts.get(receipt_id)
        if prior is not None:
            if prior != rec:
                raise ValueError('conflicting_duplicate_receipt')
            return {'result':'DUPLICATE_NOOP','generation':prior.generation}
        self.receipts[receipt_id]=rec
        return {'result':'INSTALLED','generation':self.generation}

    def advance_relevance(self, relevant_tiles):
        if not self.initialized:
            raise ValueError('advance_before_initialize')
        rel=norm_tiles(relevant_tiles)
        if rel == self.current_relevant:
            return {'result':'NOOP_SAME_RELEVANCE','generation':self.generation}
        self.generation += 1
        self.current_relevant=rel
        return {'result':'ADVANCED','generation':self.generation}

    def try_gate(self, changed_tiles, critical_tiles, receipt_id:str,
                 claimed_scope:str|None=None, claimed_generation:int|None=None):
        changed=norm_tiles(changed_tiles)
        critical=norm_tiles(critical_tiles)
        if not isinstance(receipt_id,str) or not receipt_id:
            raise ValueError('bad_gate_receipt_id')
        rec=self.receipts.get(receipt_id)
        action='FORWARD_FULL_CURRENT'; reason='MISSING_RECEIPT'
        if rec is not None:
            scope=rec.scope if claimed_scope is None else claimed_scope
            gen=rec.generation if claimed_generation is None else claimed_generation
            if scope != self.scope or scope != rec.scope:
                reason='WRONG_SCOPE_RECEIPT'
            elif not isinstance(gen,int) or gen < 1 or gen != rec.generation:
                reason='RECEIPT_IDENTITY_MISMATCH'
            elif rec.generation != self.generation:
                reason='STALE_RELEVANCE_GENERATION'
            elif changed & critical:
                reason='CRITICAL_CHANGE'
            elif changed & self.current_relevant:
                reason='CURRENT_RELEVANT_CHANGE'
            else:
                action='SUPPRESS_EXACT_IRRELEVANT'; reason='CURRENT_IRRELEVANT_CHANGE'
        if action.startswith('SUPPRESS'):
            self.suppressions += 1
        else:
            self.forwards += 1
        return {'action':action,'reason':reason,'generation':self.generation}

    def snapshot(self):
        return {
            'scope':self.scope,'generation':self.generation,'initialized':self.initialized,
            'current_relevant':sorted(self.current_relevant),
            'receipts':{k:{'receipt_id':v.receipt_id,'scope':v.scope,'generation':v.generation,'relevant_tiles':sorted(v.relevant_tiles)} for k,v in sorted(self.receipts.items())},
            'suppressions':self.suppressions,'forwards':self.forwards,
        }
