"""Pure information-limited reporting, never action authority."""
import json
import sys


def report(view, policy):
    if policy not in ('ZIP_ORDER', 'ORDER_POSSIBLE'):
        raise ValueError('unknown policy')
    out={'status':'UNKNOWN','effects':[], 'authority':False,'task_success':None}
    if (type(view) is not dict or set(view)!= {'session','requests','effects','sealed','ordered','at_most_one'}
        or type(view['session']) is not str or not view['session'].strip()
        or any(view[k] is not True for k in ('sealed','ordered','at_most_one'))):
        return out
    req=view['requests']; effects=view['effects']
    if (type(req) is not list or not 1<=len(req)<=32 or
        any(type(x) is not str or not x.strip() for x in req) or len(set(req))!=len(req)
        or type(effects) is not list or len(effects)>len(req)):
        return out
    for j,e in enumerate(effects,1):
        if (type(e) is not dict or set(e)!= {'effect_id','before','after'} or
            e['effect_id']!=f'effect-{j}' or type(e['before']) is not int or
            type(e['after']) is not int or e['before']!=j-1 or e['after']!=j):
            return out
    n,k=len(req),len(effects)
    for j,e in enumerate(effects):
        possible=req[j:j+1] if policy=='ZIP_ORDER' else req[j:n-k+j+1]
        out['effects'].append({'effect_id':e['effect_id'],'possible':possible,
                              'status':'UNIQUE' if len(possible)==1 else 'AMBIGUOUS'})
    out['status']='COMPLETE_REPORT'
    return out

if __name__=='__main__':
    # Only this explicitly delimited input file is read. No app/mask/raw access.
    with open(sys.argv[1]) as f: v=json.load(f)
    print(json.dumps(report(v,sys.argv[2]),sort_keys=True,indent=2))
