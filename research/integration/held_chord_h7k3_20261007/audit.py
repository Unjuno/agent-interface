"""Raw-only h7k3 checker. Imports no Xlib, backend, candidate or runner."""
import hashlib
import json
from pathlib import Path
import sys

CONDITIONS = ('NO_HOLD','SHIFT_SAME','SHIFT_ALIAS','CTRL_DISJOINT','SHIFT_TEXT_UPPER','SHIFT_ALREADY_RELEASED')
OVERLAP = {'SHIFT_SAME','SHIFT_ALIAS','SHIFT_TEXT_UPPER'}


def audit(rows, root=None, full=True):
    errors=[]
    checks=0
    def need(ok, message):
        nonlocal checks
        checks+=1
        if not ok: errors.append(message)
    pairs=[]
    sessions=[]
    outcomes=[]
    for r in rows:
        tag=r.get('session','missing')
        def ck(ok,text): need(ok,tag+':'+text)
        c,v=r.get('condition'),r.get('variant')
        pairs.append((c,v));sessions.append(tag)
        ck(c in CONDITIONS and v in ('current','proposal'),'case identity')
        if c not in CONDITIONS or v not in ('current','proposal'):continue
        ck('error' not in r and not r.get('cleanup_errors'),'no hidden execution error')
        ck(r.get('core_valid') is True and r.get('task_success') is None,'contract scope')
        ck(r.get('route')=='backend_methods_not_public_dispatch','route')
        ck(r.get('authority')=='fixture-only','authority')
        codes=r['keycodes'];shift,ctrl,b=codes['SHIFT'],codes['CTRL'],codes['b']
        ck(codes['Shift_L']==shift,'alias is same server code')
        ck(all(type(x) is int and 8<=x<256 for x in codes.values()),'keycode types')
        ck(len({shift,ctrl,codes['a'],b})==4,'distinct test keys')
        s=r['steps'];ck([x['label'] for x in s]==['initial','before_chord','after_chord','after_b','final'],'stages')
        if len(s)!=5:continue
        previous=[];end=r['started_ns']
        for step in s:
            km=step['keymap']
            ck(type(km) is list and len(km)==32 and all(type(x)is int and 0<=x<256 for x in km),'32-byte keymap')
            ck(end<=step['query_started_ns']<=step['query_ended_ns']<=step['app']['observed_ns']<=r['ended_ns'],'query order')
            end=step['app']['observed_ns']
            ev=step['app']['events']
            ck(ev[:len(previous)]==previous,'event-prefix preservation')
            ck(all(type(e['keycode'])is int and type(e['state'])is int and e['kind'] in ('press','release') for e in ev),'event shape')
            previous=ev
        ck(not any(s[0]['keymap']) and not any(s[4]['keymap']),'initial/final all-key neutrality')
        def down(step,code): return bool(step['keymap'][code//8] & (1<<(code%8)))
        expected_before_shift=c in OVERLAP
        expected_after_shift=c in OVERLAP and v=='proposal'
        ck(down(s[1],shift)==expected_before_shift,'before Shift')
        ck(down(s[1],ctrl)==(c=='CTRL_DISJOINT'),'before Ctrl')
        ck(down(s[2],shift)==expected_after_shift,'after Shift')
        ck(down(s[2],ctrl)==(c=='CTRL_DISJOINT'),'after Ctrl')
        ck(down(s[3],shift)==expected_after_shift,'post-b Shift')
        ck(down(s[3],ctrl)==(c=='CTRL_DISJOINT'),'post-b Ctrl')
        expected_mask=(1 if expected_after_shift else 0)|(4 if c=='CTRL_DISJOINT' else 0)
        bp=[e for e in s[3]['app']['events'] if e['kind']=='press' and e['keycode']==b]
        ck(len(bp)==1,'one b press')
        if bp:ck(bp[0]['state'] & 5==expected_mask,'recipient b modifier')
        ap=[e for e in s[3]['app']['events'] if e['kind']=='press' and e['keycode']==codes['a']]
        ck(len(ap)==1 and bool(ap[0]['state']&1),'one shifted a press')
        ck(r['release']['verified'] is True and r['release']['keys_down']==[] and r['release']['buttons_down']==[],'release receipt')
        ck(r['final_pointer_mask']&0x1f00==0,'final pointer buttons')
        ck(r['cleanup_release']['verified'] is True,'cleanup release')
        ck(all(r.get(x)is True for x in ['auth_removed','display_socket_removed','display_lock_removed']),'owned resources removed')
        ck({p['role'] for p in r['processes']}=={'xvfb','recipient'},'process starts')
        ck({p['role'] for p in r['exits']}=={'xvfb','recipient'},'process exits')
        for exit in r['exits']:
            ck(exit['returncode']==0,'actual child exit')
            ck(exit['pid']==next(p['pid'] for p in r['processes'] if p['role']==exit['role']),'PID binding')
        ck(s[4]['app']['events']==r['app_terminal']['events'],'terminal app event equality')
        source='upstream/backend.py' if v=='current' else 'candidate/backend.py'
        if root is not None:
            ck(hashlib.sha256((root/source).read_bytes()).hexdigest()==r['backend_sha256'],'source identity')
        outcomes.append(dict(condition=c,variant=v,prior_hold_lost=c in OVERLAP and not down(s[2],shift),
                             after_shift=down(s[2],shift),b_modifier_mask=bp[0]['state']&5 if bp else None,
                             emissions=s[4]['emissions'],app_events=len(r['app_terminal']['events'])))
    need(len(sessions)==len(set(sessions)),'unique session identities')
    need(len(pairs)==len(set(pairs)),'unique condition/policy cells')
    if full:
        need(set(pairs)=={(c,v) for c in CONDITIONS for v in ('current','proposal')} and len(rows)==12,'complete fixed12 cells')
    return dict(schema='h7k3-audit-v1',checks=checks,errors=errors,cases=len(rows),outcomes=outcomes,
                scope='same-author raw-only backend-method evidence; not task success')


def main():
    root=Path(__file__).resolve().parent
    rows=json.loads(Path(sys.argv[1]).read_text())
    result=audit(rows,root,full='--partial' not in sys.argv)
    print(json.dumps(result,sort_keys=True,indent=2))
    return 1 if result['errors'] else 0

if __name__=='__main__':raise SystemExit(main())
