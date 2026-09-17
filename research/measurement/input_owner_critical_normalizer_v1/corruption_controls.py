from normalizer import normalize_one,normalize_stream

def env(i,raw): return {'event_id':f'e{i}','seq':i,'received_ns':100+i,'session':'s','target':'t','stream':'input_owner','raw':raw}
def rel(reason='focus_changed',verified=True,buttons=None,keys=None): return {'event':'owner_release','reason':reason,'verified':verified,'buttons_down':[] if buttons is None else buttons,'keys_down':[] if keys is None else keys,'verified_ns':90,'valid_until_ns':120}
controls=[]
def reject(name,e):
    try: normalize_one(e); ok=False
    except ValueError: ok=True
    controls.append({'name':name,'rejected':ok})
reject('ordinary_admission',env(1,{'event':'input_admission'})); reject('unknown_verified_reason',env(2,rel('release'))); x=env(3,rel());x['session']=' ';reject('missing_scope',x)
assert normalize_one(env(4,rel(verified=False)))['normalization']['kind']=='SAFETY_VIOLATION';controls.append({'name':'unverified_not_laundered','rejected':True})
assert normalize_one(env(5,rel(buttons=[1])))['normalization']['kind']=='SAFETY_VIOLATION';controls.append({'name':'nonneutral_not_laundered','rejected':True})
try: normalize_stream([env(6,rel()),env(6,rel('expired'))]); dup=False
except ValueError: dup=True
controls.append({'name':'duplicate_id','rejected':dup}); assert all(x['rejected'] for x in controls); print('CORRUPTION_PASS',len(controls))
