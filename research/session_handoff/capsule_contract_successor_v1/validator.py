import json, hashlib

REQUIRED = ('session_id','task_id','uncertainty','replay_prohibited','expires_at','authority_status')
def validate(c, now, session, task):
    if not isinstance(c, dict) or any(k not in c for k in REQUIRED): return 'UNKNOWN'
    if c['session_id'] != session or c['task_id'] != task: return 'UNKNOWN'
    if c['uncertainty'] not in ('KNOWN','UNKNOWN','AMBIGUOUS'): return 'UNKNOWN'
    if c['replay_prohibited'] is not True: return 'UNKNOWN'
    if not isinstance(c['expires_at'], int) or c['expires_at'] <= now: return 'UNKNOWN'
    if c['expires_at'] > now + 300: return 'UNKNOWN'
    if c['authority_status'] != 'FRESH_ACQUISITION_REQUIRED': return 'UNKNOWN'
    return 'ADVISORY_ONLY'

base={'session_id':'s1','task_id':'t1','uncertainty':'KNOWN','replay_prohibited':True,'expires_at':110,'authority_status':'FRESH_ACQUISITION_REQUIRED'}
cases=[('valid',base,'ADVISORY_ONLY'),('missing',{},'UNKNOWN'),('wrong-session',{**base,'session_id':'s2'},'UNKNOWN'),('stale',{**base,'expires_at':99},'UNKNOWN'),('long',{**base,'expires_at':401},'UNKNOWN'),('replay',{**base,'replay_prohibited':False},'UNKNOWN'),('authority',{**base,'authority_status':'GRANTED'},'UNKNOWN'),('ambiguous',{**base,'uncertainty':'AMBIGUOUS'},'ADVISORY_ONLY')]
rows=[]
for name,c,expected in cases:
    actual=validate(c,100,'s1','t1'); rows.append((name,actual,expected)); assert actual==expected
print(json.dumps({'status':'PASS_CAPSULE_CONTRACT_MATRIX','rows':rows,'digest':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()},sort_keys=True))
