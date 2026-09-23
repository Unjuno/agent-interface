from interval_contract import Actuation, EffectEvent, Interval, ReleaseReceipt, analyze
from id_validation import analyze_validated

W=Interval(0,100)
def act(aid): return Actuation(10,ReleaseReceipt(20,25,False),[Interval(0,100)],aid)
def evt(aid,useful=True,scored=True): return EffectEvent(15,aid,scored,useful)

# Parent defects must exist before candidate scoring.
for bad in (None,'',0):
    got=analyze(W,[act(bad)],[evt(bad)])
    assert got['effects']['useful_bound']==1,(bad,got)
    try: analyze_validated(W,[act(bad)],[evt(bad)])
    except ValueError: pass
    else: raise AssertionError(('malformed_actuation_not_rejected',bad))

# Malformed non-None effect IDs reject.
for bad in ('',0,False,1.5,b'x',('x',),['x'],{'x':1}):
    try: analyze_validated(W,[act('a')],[evt(bad)])
    except ValueError: pass
    else: raise AssertionError(('malformed_effect_not_rejected',bad))

# None remains explicit unbound, never aliases a valid actuation.
base=analyze(W,[act('a')],[evt(None)])
cand=analyze_validated(W,[act('a')],[evt(None)])
assert base==cand and cand['effects']['useful_unbound']==1 and cand['effects']['useful_bound']==0

# Valid unicode and whitespace/nonempty strings remain valid by the frozen syntax rule.
for good in ('a','動作-α',' '):
    base=analyze(W,[act(good)],[evt(good)])
    cand=analyze_validated(W,[act(good)],[evt(good)])
    assert base==cand and cand['effects']['useful_bound']==1

# Existing duplicate-valid-ID rejection is unchanged.
for f in (analyze, analyze_validated):
    try: f(W,[act('dup'),act('dup')],[])
    except ValueError as e: assert 'duplicate' in str(e)
    else: raise AssertionError('duplicate_not_rejected')
print('STATIC_PASS')
