import json
from core import fixed_controls

def main():
    c=fixed_controls(); errs=[]
    for k in ('legit_current','compromised_current','replay_first'):
        if c[k].get('state')!='SELF_CONFIRMED': errs.append(k)
    if c['visible_equal'] is not True: errs.append('visible_not_equal')
    for k in ('wrong_key','retired_epoch','future_epoch','replay_second','conflict'):
        if c[k].get('state')=='SELF_CONFIRMED': errs.append(k+'_escaped')
    if c['external'].get('state')!='EXTERNAL_CONFIRMED': errs.append('external')
    if c['no_mutation'].get('state')!='NO_MUTATION': errs.append('no_mutation')
    print(json.dumps({'errors':errs,'pass':not errs,'controls':c},sort_keys=True))
    raise SystemExit(bool(errs))
if __name__=='__main__': main()
