from itertools import product
import hashlib,json

LAYERS=('binding','precondition','route','observation_cache','motor_calibration')
ROUTE=LAYERS.index('route')

def members(bits):
    return {i for i in range(len(LAYERS)) if bits & (1<<i)}

def oracle(dep_bits,change_bits):
    return not bool(members(dep_bits) & members(change_bits))

def layered(dep_bits,change_bits):
    deps=members(dep_bits); changed=members(change_bits)
    return all(i not in changed for i in deps)

def global_epoch(dep_bits,change_bits):
    return change_bits==0

def route_only(dep_bits,change_bits):
    return not bool(change_bits & (1<<ROUTE))

def classify(policy_ok,truth):
    if policy_ok and not truth: return 'STALE_ACCEPT'
    if not policy_ok and truth: return 'FALSE_INVALIDATE'
    return 'MATCH'

def run():
    stats={
      'rows':0,
      'layered_mismatch':0,'layered_stale_accept':0,'layered_false_invalidate':0,
      'global_stale_accept':0,'global_false_invalidate':0,
      'route_stale_accept':0,'route_false_invalidate':0,
    }
    h=hashlib.sha256()
    for dep_bits,change_bits in product(range(1,1<<len(LAYERS)),range(0,1<<len(LAYERS))):
        truth=oracle(dep_bits,change_bits)
        lc=layered(dep_bits,change_bits)
        gc=global_epoch(dep_bits,change_bits)
        rc=route_only(dep_bits,change_bits)
        stats['rows']+=1
        stats['layered_mismatch']+=int(lc!=truth)
        stats['layered_stale_accept']+=int(lc and not truth)
        stats['layered_false_invalidate']+=int((not lc) and truth)
        stats['global_stale_accept']+=int(gc and not truth)
        stats['global_false_invalidate']+=int((not gc) and truth)
        stats['route_stale_accept']+=int(rc and not truth)
        stats['route_false_invalidate']+=int((not rc) and truth)
        h.update(json.dumps([dep_bits,change_bits,truth,lc,gc,rc],separators=(',',':')).encode())
    directed=[]
    for i,name in enumerate(LAYERS):
        dep=1<<i
        directed.append({
          'layer':name,
          'unchanged':layered(dep,0),
          'same_layer_changed':layered(dep,1<<i),
          'oracle_unchanged':oracle(dep,0),
          'oracle_changed':oracle(dep,1<<i),
        })
    decision='PASS_LAYERED_LIFETIME_ADMISSION_CONTRACT_SCOPED'
    if not (
        stats['rows']==992 and stats['layered_mismatch']==0 and
        stats['layered_stale_accept']==0 and stats['layered_false_invalidate']==0 and
        stats['global_stale_accept']==0 and stats['global_false_invalidate']>0 and
        stats['route_stale_accept']>0 and stats['route_false_invalidate']>0 and
        all(x['unchanged'] and x['oracle_unchanged'] and (not x['same_layer_changed']) and (not x['oracle_changed']) for x in directed)
    ):
        decision='FAIL'
    return {
      'task':'LAYERED-LIFETIME-ADMISSION-CONTRACT-R0-20260918-001',
      'layers':list(LAYERS),'stats':stats,'directed':directed,
      'ledger_sha256':h.hexdigest(),'decision':decision,
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
    }

if __name__=='__main__':
    print(json.dumps(run(),indent=2,sort_keys=True))
