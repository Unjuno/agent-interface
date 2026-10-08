"""Receipt-only recipe decisions; no scenario, outcome or fixture access."""
POLICIES=('CLICK_THEN_TYPE','POST_FOCUS','HIT_AND_FOCUS','NO_TASK_INPUT')
def decide(policy,phase,expected,receipt):
    if policy not in POLICIES or phase not in ('click','type'): raise ValueError('unsupported decision')
    keys={'session','target','surface','sequence','captured_ns','geometry','hit','focus'}
    if type(receipt) is not dict or set(receipt)!=keys: return {'allow':False,'reason':'MALFORMED'}
    if any(type(receipt[k]) is not int for k in ('target','surface','sequence','captured_ns')):
        return {'allow':False,'reason':'MALFORMED'}
    if any(receipt[k]!=expected[k] for k in ('session','target','surface','geometry')):
        return {'allow':False,'reason':'BINDING_CHANGED'}
    if policy=='NO_TASK_INPUT': return {'allow':False,'reason':'CONTROL'}
    if phase=='click' and policy=='HIT_AND_FOCUS' and (type(receipt['hit']) is not int or receipt['hit']!=expected['target']):
        return {'allow':False,'reason':'HIT_NOT_TARGET'}
    if phase=='type' and policy in ('POST_FOCUS','HIT_AND_FOCUS') and (type(receipt['focus']) is not int or receipt['focus']!=expected['target']):
        return {'allow':False,'reason':'FOCUS_NOT_TARGET'}
    return {'allow':True,'reason':'RECIPE_ELIGIBLE'}
