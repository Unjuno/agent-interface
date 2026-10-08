"""Independent raw-only audit. No import of runner, actor, or policy implementation."""
from __future__ import annotations
import base64
import collections
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

SCHEDULE=('STABLE','UNRELATED','DUPLICATE','MOVED','ABSENT','DUPLICATE_FULL_UNAVAILABLE')
ARMS=('LOCAL_PATCH','GLOBAL_UNIQUENESS')
KNOWN_XVFB_STDERR_SHA256='12dcabf0449b9ff85d589b86d110c814777977daca56e7ba8ec300c5334fe397'

def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def load(root: Path) -> list[dict]:
    paths=sorted(root.glob('batch-*/*/RAW.json')) or sorted(root.glob('*/RAW.json'))
    return [{'raw':json.loads(p.read_text()),
             'journal':[json.loads(line) for line in (p.parent/'actor.jsonl').read_text().splitlines()],
             'stderr':{n:(p.parent/n).read_text() for n in ('actor.stderr','policy.stderr','xvfb.stderr')}}
            for p in paths]

def analyze(records: list[dict], construction: bool=False, sources: dict|None=None) -> dict:
    errors=[]; checks=0; metrics=[]
    def check(ok: bool, name: str) -> None:
        nonlocal checks
        checks+=1
        if not ok: errors.append(name)
    expected=[]
    if construction:
        expected=[('construction-0-00',0,'STABLE','LOCAL_PATCH'),
                  ('construction-0-01',0,'MOVED','LOCAL_PATCH'),
                  ('construction-0-02',0,'DUPLICATE','GLOBAL_UNIQUENESS'),
                  ('construction-0-03',0,'ABSENT','GLOBAL_UNIQUENESS')]
    else:
        for rep in (0,1):
            sched=[(s,a) for s in (SCHEDULE if rep==0 else SCHEDULE[::-1])
                   for a in (ARMS if rep==0 else ARMS[::-1])]
            expected.extend((f'formal-{rep}-{i:02d}',rep,s,a) for i,(s,a) in enumerate(sched))
    keys=[(r.get('raw',{}).get('id'),r.get('raw',{}).get('rep'),r.get('raw',{}).get('scenario'),
           r.get('raw',{}).get('arm')) for r in records]
    check(collections.Counter(keys)==collections.Counter(expected),'denominator/schedule')
    check(len({k[0] for k in keys})==len(keys),'unique cases')
    for item in records:
        rec=item.get('raw',{}); tag=str(rec.get('id','missing'))
        def ck(ok: bool, name: str) -> None: check(ok,tag+':'+name)
        try:
            ck(rec['status']=='COMPLETE','complete')
            ck(type(rec['rep']) is int and rec['rep'] in (0,1),'rep type')
            ck(type(rec['binding_generation']) is int and rec['binding_generation']==1,'generation type')
            ck(rec['socket_absent'] is True and rec['lock_absent'] is True and rec['auth_removed'] is True,'cleanup')
            ck(rec['auth']['scheme']=='MIT-MAGIC-COOKIE-1','auth scheme')
            ck(not any(k in rec for k in ('emergency_release','cleanup_error','exception')),'no hidden failure')
            for n in ('actor_process','policy_process','xvfb_process'):
                ck(type(rec[n]['exit']) is int and rec[n]['exit']==0,n+' exit')
                ck(type(rec[n]['pid']) is int and rec[n]['pid']>0,n+' pid')
            pids=[rec[n]['pid'] for n in ('actor_process','policy_process','xvfb_process')]+[rec['controller_pid']]
            ck(len(set(pids))==4,'separate live processes')
            ck(rec['actor_process']['pid']==rec['ready']['pid'],'ready process')
            ck(not item['stderr']['actor.stderr'] and not item['stderr']['policy.stderr'],
               'actor/policy stderr empty')
            ck(digest(item['stderr']['xvfb.stderr'].encode('utf-8'))==KNOWN_XVFB_STDERR_SHA256,
               'known Xvfb xkbcomp warning only')
            xa=rec['xvfb_process']['argv']
            ck('-displayfd' in xa and '-auth' in xa and '-ac' not in xa and ['-nolisten','tcp']==xa[xa.index('-nolisten'):xa.index('-nolisten')+2],'owned Xvfb command')
            ck(rec['window_geometry']=={'width':320,'height':120},'window domain')
            if sources is not None: ck(rec['sources']==sources,'frozen source identity')
            else: ck(rec['sources']==records[0]['raw']['sources'],'construction source identity')
            xid=rec['ready']['window']
            binding={'session':tag,'window':xid,'generation':1,'domain':[0,0,320,120]}
            cr,cp=rec['cold']['request'],rec['cold']['response']
            wr,wp=rec['warm']['request'],rec['warm']['response']
            ck(set(cr)=={'mode','binding','full'},'cold input boundary')
            ck(set(wr)=={'mode','arm','binding','cache','full','patch'},'warm input boundary')
            ck(cr['mode']=='cold' and wr['mode']=='warm' and wr['arm']==rec['arm'],'request mode')
            ck(all(x['binding']==binding for x in (cr,cp,wr,wp)),'binding equality')
            ck(all(type(x['binding']['generation']) is int for x in (cr,cp,wr,wp)),'binding strict generation')
            ck(cp['authority_granted'] is False and wp['authority_granted'] is False,'authority')
            def image(im: dict, rect: list, role: str) -> bytes:
                b=base64.b64decode(im['b64'],validate=True)
                ck(im['rect']==rect and [im['w'],im['h']]==rect[2:],'image domain '+role)
                ck(im['depth']==24 and type(im['depth']) is int and len(b)==rect[2]*rect[3]*4,'pixel ABI '+role)
                ck(im['nbytes']==len(b) and type(im['nbytes']) is int and digest(b)==im['sha256'],'image digest '+role)
                ck(im['role']==role and im['window']==xid,'image provenance '+role)
                ck(type(im['start_ns']) is int and type(im['end_ns']) is int and 0<im['start_ns']<=im['end_ns'],'image time '+role)
                return b
            cold=image(cr['full'],[0,0,320,120],'candidate_cold')
            witness=image(rec['witness'],[0,0,320,120],'scorer_only')
            final=image(rec['final_witness'],[0,0,320,120],'scorer_only_final')
            ck(witness==final,'quiescent bytes')
            def groups(b: bytes) -> list[list[int]]:
                # Independent algorithm: flood-fill 4-connected green pixels, not row runs.
                remaining={(i%320,i//320) for i in range(320*120) if b[4*i:4*i+3]==bytes((0,255,0))}
                boxes=[]
                while remaining:
                    seed=remaining.pop(); component={seed}; stack=[seed]
                    while stack:
                        x,y=stack.pop()
                        for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                            if q in remaining:
                                remaining.remove(q);component.add(q);stack.append(q)
                    x0=min(x for x,y in component);y0=min(y for x,y in component)
                    x1=max(x for x,y in component)+1;y1=max(y for x,y in component)+1
                    ck(len(component)==256 and x1-x0==16 and y1-y0==16,'rectangular target component')
                    boxes.append([x0,y0,x1-x0,y1-y0])
                return sorted(boxes)
            ck(groups(cold)==[[32,48,16,16]],'cold one target')
            g=groups(witness)
            wanted={'STABLE':[[32,48,16,16]],'UNRELATED':[[32,48,16,16]],
                    'DUPLICATE':[[32,48,16,16],[240,48,16,16]],'MOVED':[[240,48,16,16]],
                    'ABSENT':[],'DUPLICATE_FULL_UNAVAILABLE':[[32,48,16,16],[240,48,16,16]]}[rec['scenario']]
            ck(g==wanted,'directed exposure')
            # Independently reconstruct all declared foreground/background pixels, including nuisance.
            for label,b,boxes,nuisance in (('cold',cold,[[32,48,16,16]],False),('warm',witness,wanted,rec['scenario']=='UNRELATED')):
                expected_rgb=bytearray(320*120*3)
                for x,y,w,h in boxes:
                    for yy in range(y,y+h):
                        for xx in range(x,x+w):expected_rgb[3*(yy*320+xx)+1]=255
                if nuisance:
                    for yy in range(8,20):
                        for xx in range(100,112):expected_rgb[3*(yy*320+xx)]=255
                actual=b''.join(b[i:i+3] for i in range(0,len(b),4))
                ck(actual==expected_rgb,'complete '+label+' pixels')
            patch_expected=b''.join(cold[4*((48+y)*320+32):4*((48+y)*320+48)] for y in range(16))
            cache={'rect':[32,48,16,16],'patch_sha':digest(patch_expected),'binding':binding}
            ck(cp['cache']==cache and wr['cache']==cache,'cold/warm cache')
            ck(cp['disposition']=='CACHED' and cp['point'] is None and cp['scan_pixels']==38400,'cold output')
            ck(type(cp['scan_pixels']) is int and type(wp['scan_pixels']) is int,'scan type')
            available=rec['scenario']!='DUPLICATE_FULL_UNAVAILABLE'
            ck(rec['full_available'] is available,'availability')
            scans=0; local_hit=False; acquired=0
            if rec['arm']=='LOCAL_PATCH':
                pb=image(wr['patch'],[32,48,16,16],'candidate_patch')
                warm_crop=b''.join(witness[4*((48+y)*320+32):4*((48+y)*320+48)] for y in range(16))
                ck(pb==warm_crop,'current patch')
                local_hit=(pb==patch_expected);scans+=256;acquired+=256
                need_full=not local_hit and available
            else:
                ck(wr['patch'] is None,'global no patch')
                need_full=available
            ck((wr['full'] is not None)==need_full,'full acquisition request')
            if wr['full'] is not None:
                fb=image(wr['full'],[0,0,320,120],'candidate_full')
                ck(fb==witness,'candidate current full bytes');scans+=38400;acquired+=38400
            if local_hit:point=[40,56];reason='LOCAL_HIT'
            elif not available:point=None;reason='FULL_UNAVAILABLE'
            elif len(g)==1:point=[g[0][0]+8,g[0][1]+8];reason='FULL_UNIQUE'
            else:point=None;reason='AMBIGUOUS' if g else 'ABSENT'
            ck(wp['point']==point and wp['disposition']==('PROPOSE' if point else 'YIELD') and wp['reason']==reason,'policy semantics')
            ck(wp['cache'] is None and wp['scan_pixels']==scans,'warm output accounting')
            if wp['point'] is not None: ck(all(type(v) is int for v in wp['point']),'point strict ints')
            emitted=point is not None
            ck(len(rec['input'])==(2 if emitted else 0),'input cardinality')
            if emitted:
                ck([e['type'] for e in rec['input']]==[4,5],'press release order')
                for e in rec['input']:
                    ck(e['button']==1 and [e['x'],e['y']]==point,'driver point')
                    ck(rec['warm_response_ns']<=e['start_ns']<=e['end_ns']<=rec['post_neutral']['ns'],'driver timing')
            journal=item['journal']; je=[j for j in journal if j['kind']=='input']; jf=[j for j in journal if j['kind']=='effect']
            ck([j['ns'] for j in journal]==sorted(j['ns'] for j in journal),'journal order')
            ck(all(j['pid']==rec['actor_process']['pid'] for j in journal),'journal PID')
            ck(journal[0]['kind']=='ready' and journal[-1]['kind']=='exit','journal lifecycle')
            cmds=[j['command'] for j in journal if j['kind']=='command']
            ck(cmds==[{'op':'draw','id':1,'targets':[[32,48,16,16]],'nuisance':False},
                      {'op':'draw','id':2,'targets':wanted,'nuisance':rec['scenario']=='UNRELATED'},
                      {'op':'snapshot','id':3},{'op':'close','id':4}],'actor commands')
            ck(len(je)==(2 if emitted else 0) and len(jf)==(1 if emitted else 0),'observed events/effects')
            ck(je==rec['final_snapshot']['events'] and jf==rec['final_snapshot']['effects'],'snapshot equals independent journal')
            ck(rec['close']['events']==je and rec['close']['effects']==jf,'closed effect boundary')
            for name in ('cold_draw','warm_draw'):
                ck(rec[name]['events']==[] and rec[name]['effects']==[],'no earlier input '+name)
            if emitted:
                ck([e['type'] for e in je]==[4,5],'app press release order')
                ck(all(e['button']==1 and [e['x'],e['y']]==point and e['send_event'] is False and e['window']==xid for e in je),'app delivery')
                ck(rec['input'][0]['start_ns']<=je[0]['ns']<=je[1]['ns']<=jf[0]['ns']<=rec['final_snapshot']['ns'],'app effect timing')
                hit=next((box for box in g if box[0]<=point[0]<box[0]+16 and box[1]<=point[1]<box[1]+16),None)
                ck(jf[0]['target']==hit and jf[0]['ordinal']==1,'effect target')
            for phase in ('pre_neutral','post_neutral'):
                n=rec[phase];ck(n['keymap']==[0]*32 and n['button_mask']==0 and type(n['button_mask']) is int,'neutral '+phase)
            ck(rec['cold_draw']['ns']<=cr['full']['start_ns']<=cr['full']['end_ns']<=rec['warm_draw']['ns']<=rec['witness']['start_ns']<=rec['witness']['end_ns']<=rec['warm_request_ns']<=rec['warm_response_ns']<=rec['final_snapshot']['ns'],'stage order')
            wire=rec['policy_process']['wire']
            ck([w['direction'] for w in wire]==['send','recv','send','recv'],'policy wire order')
            ck([json.loads(w['text']) for w in wire]==[cr,cp,wr,wp],'policy exact wire')
            aw=rec['actor_process']['wire']
            ck([json.loads(w['text']) for w in aw if w['direction']=='send']==cmds,'actor exact command wire')
            replies=[j['reply'] for j in journal if j['kind']=='reply']
            ck([json.loads(w['text']) for w in aw if w['direction']=='recv'][1:]==replies,'actor exact reply wire')
            unsafe=emitted and (len(g)!=1 or not available)
            if rec['arm']=='GLOBAL_UNIQUENESS':ck(not unsafe,'candidate safe refusal')
            metrics.append({'id':tag,'arm':rec['arm'],'scenario':rec['scenario'],'actual_targets':len(g),
                            'input':int(emitted),'effects':len(jf),'unsafe':int(unsafe),
                            'warm_scan_pixels':scans,'warm_acquired_pixels':acquired,
                            'warm_acquired_bytes':acquired*4,'cold_scan_pixels':38400,
                            'safe_incompletion':int(not emitted)})
        except Exception as exc:
            ck(False,'malformed evidence '+type(exc).__name__+': '+str(exc))
    totals={a:{k:sum(m[k] for m in metrics if m['arm']==a) for k in
            ('input','effects','unsafe','warm_scan_pixels','warm_acquired_pixels','warm_acquired_bytes','cold_scan_pixels','safe_incompletion')}
            for a in ARMS}
    if not construction:
        check(totals['LOCAL_PATCH']['unsafe']==4,'weak ambiguity exposed four times')
        check(totals['GLOBAL_UNIQUENESS']['unsafe']==0,'candidate unsafe zero')
        check(totals['GLOBAL_UNIQUENESS']['effects']==6,'candidate stable/nuisance/moved effects')
        check(totals['GLOBAL_UNIQUENESS']['safe_incompletion']==6,'candidate six safe incompletions')
    return {'status':'PASS' if not errors else 'REJECT','checks':checks,'errors':errors,
            'case_count':len(records),'metrics':metrics,'totals':totals,'construction':construction}

if __name__=='__main__':
    root=Path(sys.argv[1]); construction='--construction' in sys.argv
    output=Path(sys.argv[sys.argv.index('--output')+1]) if '--output' in sys.argv else None
    freeze=Path(__file__).with_name('FREEZE.json')
    sources=None if construction else json.loads(freeze.read_text())['sources']
    answer=analyze(load(root),construction,sources)
    rendered=json.dumps(answer,sort_keys=True,indent=2)+'\n'
    if output is not None:
        with output.open('x',encoding='utf-8') as f:f.write(rendered);f.flush()
    print(rendered,end='')
    raise SystemExit(0 if answer['status']=='PASS' else 1)
