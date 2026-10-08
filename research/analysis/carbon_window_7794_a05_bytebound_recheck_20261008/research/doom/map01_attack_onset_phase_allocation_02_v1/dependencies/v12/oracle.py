def valid_text(x): return type(x) is str and bool(x.strip())

def press_status(owner_owned_before, pre_down, post_down, owner_owned_after):
    if owner_owned_before: return 'OWNER_ALREADY_HELD'
    if pre_down: return 'PREEXISTING_PHYSICAL_DOWN'
    if post_down and owner_owned_after: return 'CONFIRMED_PHYSICAL_DOWN'
    return 'PRESS_UNCONFIRMED'

def release_status(owner_owned, pre_down, post_down):
    if not owner_owned: return 'FOREIGN_OR_STALE_DOWN' if pre_down else 'NOOP_ALREADY_UP'
    if not pre_down: return 'OWNER_PHYSICAL_MISMATCH'
    if not post_down: return 'CONFIRMED_PHYSICAL_UP'
    return 'RELEASE_UNCONFIRMED'

class IdentityOracle:
    def __init__(self, owner_id='ownerA'):
        self.owner_id=owner_id; self.gen=0; self.active={}; self.retired=set()
    def down(self,code,key,intent,owner_owned,confirmed):
        if code in self.active:
            ci,ck,aid=self.active[code]
            if not valid_text(intent) or (ci,ck)!=(intent,key): return ('LINEAGE_MISMATCH',None)
            if owner_owned: return ('ACTIVE_REUSED',aid)
            return ('ACTIVE_WITHOUT_OWNER_HOLD',None)
        if owner_owned: return ('OWNER_HOLD_IDENTITY_MISSING',None)
        if not confirmed: return ('UNCONFIRMED_DOWN_NO_ID',None)
        if not valid_text(intent): return ('LINEAGE_UNAVAILABLE',None)
        self.gen+=1; aid=f'{self.owner_id}:g{self.gen}:{key}'
        if aid in self.retired: raise AssertionError('oracle retired reuse')
        self.active[code]=(intent,key,aid); return ('MINTED',aid)
    def up(self,code,key,intent,confirmed):
        if not confirmed: return ('UNCONFIRMED_UP_NO_CHANGE',None)
        cur=self.active.get(code)
        if cur is None: return ('NO_ACTIVE_ID',None)
        ci,ck,aid=cur
        if not valid_text(intent) or (ci,ck)!=(intent,key): return ('LINEAGE_MISMATCH',None)
        del self.active[code]; self.retired.add(aid); return ('RETIRED',aid)
    def cleanup_verified(self):
        for _,_,aid in self.active.values(): self.retired.add(aid)
        self.active.clear()
    def snapshot(self): return (self.gen,tuple(sorted(self.active.items())),tuple(sorted(self.retired)))
