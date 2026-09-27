"""Raw-only independent checker. No runner/policy/backend/Tk/Xlib imports."""
import argparse,hashlib,json,sys,zlib
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()
def read(path): return json.loads(path.read_text())
class Checks:
    def __init__(self): self.errors=[]; self.n=0
    def __call__(self,ok,msg):
        self.n+=1
        if not ok:self.errors.append(msg)

def expected_rows():
    ps=['CLICK_THEN_TYPE','POST_FOCUS','HIT_AND_FOCUS']; rows=[]
    for rep in range(2):
        for scenario in ['CLEAR','COVER_BEFORE','COVER_AFTER','UNRELATED']:
            order=ps[rep:]+ps[:rep]
            for pol in order: rows.append({'rep':rep,'scenario':scenario,'policy':pol,'index':len(rows)})
    for scenario in ['CLEAR','COVER_BEFORE']: rows.append({'rep':0,'scenario':scenario,'policy':'NO_TASK_INPUT','index':len(rows)})
    return rows

def outcome(cfg):
    pol=cfg['policy']; s=cfg['scenario']
    clicked=pol!='NO_TASK_INPUT' and not (pol=='HIT_AND_FOCUS' and s=='COVER_BEFORE')
    covered=s in ('COVER_BEFORE','COVER_AFTER')
    typed=clicked and (not covered or pol=='CLICK_THEN_TYPE')
    return dict(click=int(clicked),typed=int(typed),a='7' if typed and not covered else '',b='7' if typed and covered else '',counter=int(clicked and covered))

def case_audit(root,cfg):
    root=Path(root); c=Checks(); metrics={}
    try:
        r=read(root/'record.json'); exp=outcome(cfg); ids=r['initial']['ids']; sid=r['session']; pol=cfg['policy']
        c(r['config']==cfg,'config'); c(r['execution']=='COMPLETE','execution')
        c(type(r['app_exit']) is int and r['app_exit']==0 and type(r['observed_app_exit']) is int and r['observed_app_exit']==0,'app_exit')
        c(r['app_stderr']=='' and (root/'app.stderr').read_text()=='','stderr')
        c(r.get('stdout_tail')=='','stdout_tail')
        c(type(sid) is str and len(sid)==32,'opaque_session')
        c(len(set(ids.values()))==4 and all(type(x) is int and x>0 for x in ids.values()),'native_ids')
        c(r['initial']['a']==r['initial']['b']=='' and r['initial']['counter']==0,'initial_values')
        c(r['initial']['focus']==ids['b'],'initial_recipient')
        geometry=r['initial']['geometry']
        c(r['geometry_before']==geometry==r['geometry_after'],'native_geometry_invariant')
        previous=0
        for stage in ['initial','pre','before_click','after_click','final','close']:
            snap=r[stage]
            c(snap['session']==sid and snap['ids']==ids and snap['pid']==r['initial']['pid'],'identity:'+stage)
            c(snap['geometry']==geometry,'geometry:'+stage)
            c(type(snap['captured_ns']) is int and snap['captured_ns']>previous,'time:'+stage);previous=snap['captured_ns']
        # Native pointer hierarchy comes from a separate X connection; Tk's own
        # hit-test is an independent cross-check, not input to this oracle.
        for stage in ['pre','before_click','after_click']:
            obs=r[stage+'_observer']; chain=obs['chain']
            c(bool(chain) and chain[-1]['window']==obs['leaf'] and chain[-1]['child']==0,'hit_chain:'+stage)
            for i in range(1,len(chain)): c(chain[i-1]['child']==chain[i]['window'],'chain_join:'+stage)
            c(obs['leaf']==r[stage]['hit'],'tk_native_hit_agreement:'+stage)
            c(all(v['x']==geometry['x']+geometry['width']//2 and v['y']==geometry['y']+geometry['height']//2 for v in chain),'pointer_point:'+stage)
        c(r['pre_observer']['leaf']==(ids['cover'] if cfg['scenario']=='COVER_BEFORE' else ids['a']),'pre_hit_control')
        c(r['before_click_observer']['leaf']==(ids['cover'] if cfg['scenario'] in ('COVER_BEFORE','COVER_AFTER') else ids['a']),'actual_hit_control')
        calls=r['calls']; buttons=[x for x in calls if x['method']=='pointer_button']; keys=[x for x in calls if x['method']=='key_chord']
        c([x['args'] for x in buttons]==([['left',True],['left',False]] if exp['click'] else []),'button_requests')
        c([x['args'] for x in keys]==([[['7']]] if exp['typed'] else []),'key_requests')
        c([x['method'] for x in calls].count('pointer_move')==1,'common_motion')
        last=0
        for call in calls:
            c(type(call['started_ns']) is int and type(call['ended_ns']) is int and last<=call['started_ns']<=call['ended_ns'],'call_order')
            last=call['ended_ns']
        c(calls[-1]['emissions']==1+2*exp['click']+2*exp['typed'],'native_emission_count')
        c(len(r['decisions'])==1+exp['click'],'decision_denominator')
        for n,d in enumerate(r['decisions']):
            stage='pre' if d['phase']=='click' else 'after_click'; q=d['receipt']; s=r[stage]
            c(set(q)=={'session','target','surface','sequence','captured_ns','geometry','hit','focus'},'decision_allowlist')
            c(q['session']==sid and q['target']==ids['a'] and q['geometry']==geometry and q['captured_ns']==s['captured_ns'] and q['focus']==s['focus'] and q['hit']==r[stage+'_observer']['leaf'],'receipt_binding')
            c(q['sequence']==n+1 and type(q['sequence']) is int,'receipt_sequence')
            c(type(d['decided_ns']) is int and q['captured_ns']<d['decided_ns'],'decision_time')
            if pol=='NO_TASK_INPUT': wanted=False;reason='CONTROL'
            elif d['phase']=='click':
                wanted=(pol!='HIT_AND_FOCUS' or q['hit']==ids['a']);reason='RECIPE_ELIGIBLE' if wanted else 'HIT_NOT_TARGET'
            else:
                wanted=(pol=='CLICK_THEN_TYPE' or q['focus']==ids['a']);reason='RECIPE_ELIGIBLE' if wanted else 'FOCUS_NOT_TARGET'
            c(d['result']=={'allow':wanted,'reason':reason},'receipt_only_decision')
        if buttons:c(r['decisions'][0]['decided_ns']<buttons[0]['started_ns'],'check_before_click')
        if keys:c(r['decisions'][-1]['decided_ns']<keys[0]['started_ns'],'focus_check_before_key')
        rpcs=r['rpcs']; parsed_out=[json.loads(x) for x in (root/'app.stdout').read_text().splitlines()]; parsed_in=[json.loads(x) for x in (root/'app.stdin').read_text().splitlines()]
        c(parsed_out[0]==r['ready'] and parsed_out[1:]==[x['response'] for x in rpcs],'stdout_binding')
        c(parsed_in==[x['request'] for x in rpcs],'stdin_binding')
        for i,x in enumerate(rpcs):
            c(x['request']['id']==x['response']['id']==i+1,'rpc_id')
            c(x['sent_ns']<x['response']['snapshot']['captured_ns']<x['received_ns'],'rpc_clock')
        configs=[x for x in rpcs if x['request']['op']=='cover']
        c(len(configs)==int(cfg['scenario']!='CLEAR'),'layout_command_count')
        if configs:
            c(configs[0]['request']['mode']==('unrelated' if cfg['scenario']=='UNRELATED' else 'target'),'layout_mode')
            if cfg['scenario']=='COVER_AFTER':
                c(r['decisions'][0]['decided_ns']<configs[0]['sent_ns']<configs[0]['received_ns'],'after_check_schedule')
            else:c(configs[0]['received_ns']<r['decisions'][0]['decided_ns'],'before_check_schedule')
        events=[json.loads(x) for x in (root/'app-events.jsonl').read_text().splitlines()]
        c([x['seq'] for x in events]==list(range(1,len(events)+1)),'event_sequence')
        c(all(x['session']==sid for x in events),'event_session')
        c(all(a['monotonic_ns']<=b['monotonic_ns'] for a,b in zip(events,events[1:])),'event_monotonic')
        c([e['request'] for e in events if e['kind']=='rpc']==parsed_in,'app_request_join')
        native=[e for e in events if e['kind']=='native']; callbacks=[e for e in events if e['kind']=='callback']; values=[e for e in events if e['kind']=='value']
        for e_type,count in [('4',exp['click']),('5',exp['click']),('2',exp['typed']),('3',exp['typed'])]:
            es=[e for e in native if e['event']==e_type]; c(len(es)==count,'native_count:'+e_type)
            if es:
                which='cover' if exp['counter'] and e_type in ('4','5') else ('a' if exp['a'] else 'b')
                c(all(e['widget']=='.'+which and e['xid']==ids[which] for e in es),'native_destination:'+e_type)
        c(len(callbacks)==exp['counter'] and [e['counter'] for e in callbacks]==list(range(1,exp['counter']+1)),'callback_count')
        c([(e['field'],e['value']) for e in values]==([('a' if exp['a'] else 'b','7')] if exp['typed'] else []),'ordinary_text_effect')
        app_final=read(root/'app-final.json'); c(app_final==r['close'],'application_final_file')
        for k in ('a','b','counter'): c(r['final'][k]==app_final[k]==exp[k],'final_effect:'+k)
        for name in ('release','cleanup_release'):
            c(r[name]['verified'] is True and r[name]['keys_down']==[] and r[name]['buttons_down']==[],'release:'+name)
        finalobs=r['final_observer']; c(len(finalobs['keymap'])==32 and all(type(k) is int and k==0 for k in finalobs['keymap']) and finalobs['button_mask']==0,'independent_neutral')
        for capname,wanted in [('before_capture',0x112233),('after_capture',0x55aa33 if exp['counter'] else 0x112233)]:
            cap=r[capname]; raw=zlib.decompress((root/cap['file']).read_bytes());c(len(raw)==cap['size']==640*360*4 and sha(raw)==cap['sha256'],'capture_bytes:'+capname)
            c(cap['width']==640 and cap['height']==360 and cap['bits_per_pixel']==32 and cap['byte_order']==0 and cap['masks']==[0xff0000,0xff00,0xff],'capture_format')
            x,y=cap['marker_xy']; pixels=[int.from_bytes(raw[((y+j)*640+x+i)*4:((y+j)*640+x+i)*4+4],'little') & 0xffffff for j in range(10) for i in range(10)]
            c(all(px==wanted for px in pixels),'independent_marker:'+capname)
        metrics={'index':cfg['index'],'policy':pol,'scenario':cfg['scenario'],'a':app_final['a'],'b':app_final['b'],'counter':app_final['counter'],'clicks':len(buttons)//2,'typed':len(keys)}
    except (OSError,KeyError,ValueError,TypeError,IndexError,zlib.error) as e:c(False,'incomplete:'+type(e).__name__+':'+str(e))
    return {'errors':c.errors,'checks':c.n,'metrics':metrics}

def audit(here,construction=None):
    here=Path(here); c=Checks(); rows=[]
    if construction is not None:
        for cfg in expected_rows()[:12]:
            result=case_audit(Path(construction)/f"case-{cfg['index']:02d}",cfg);c.errors.extend(f"case{cfg['index']}:"+e for e in result['errors']); c.n+=result['checks'];rows.append(result['metrics'])
    else:
        try:
            freeze=read(here/'FREEZE.json')
            for n,h in freeze['sha256'].items():c(sha((here/n).read_bytes())==h,'frozen_source:'+n)
            for bi in range(3):
                folder=here/'results'/f'formal-batch-{bi:02d}'; stamp=read(folder.with_suffix('.execution.json')); start=read(folder/'START.json'); end=read(folder/'END.json')
                batch=expected_rows()[9*bi:min(9*bi+9,26)]
                c(type(stamp['returncode']) is int and stamp['returncode']==0 and stamp['timed_out'] is False,'outer_exit')
                c(stamp['child_pid']==start['pid'] and stamp['started_ns']<start['monotonic_ns']<end['monotonic_ns']<stamp['ended_ns'],'outer_identity_clock')
                c(start['schedule']==batch and start['mode']=='formal' and start['batch']==bi,'frozen_batch')
                c(end['error'] is None and type(end['server_exit']) is int and end['server_exit']==0 and end['auth_removed'] is True and end['socket_removed'] is True,'server_cleanup')
                c(end['completed_cases']==len(batch),'batch_count')
                c(sorted(p.name for p in folder.glob('case-*'))==[f"case-{r['index']:02d}" for r in batch],'case_files')
                for cfg in batch:
                    result=case_audit(folder/f"case-{cfg['index']:02d}",cfg);c.errors.extend(f"case{cfg['index']}:"+e for e in result['errors']);c.n+=result['checks'];rows.append(result['metrics'])
            c(len(rows)==26,'denominator')
        except (OSError,KeyError,TypeError,ValueError) as e:c(False,'allocation_incomplete:'+str(e))
    totals={p:{'cases':sum(r.get('policy')==p for r in rows),'correct_a':sum(r.get('a')=='7' for r in rows if r.get('policy')==p),'wrong_b':sum(r.get('b')=='7' for r in rows if r.get('policy')==p),'cover_callbacks':sum(r.get('counter',0) for r in rows if r.get('policy')==p)} for p in ('CLICK_THEN_TYPE','POST_FOCUS','HIT_AND_FOCUS','NO_TASK_INPUT')}
    return {'decision':'PASS_ACTIVATION_HIT_TARGET_BOUNDARY_SCOPED' if not c.errors else 'HOLD_EVIDENCE_OR_GATE_FAILURE','errors':c.errors,'checks':c.n,'rows':rows,'totals':totals,'scope':'construction' if construction else 'formal'}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('--construction');args=a.parse_args();result=audit(args.source,args.construction);print(json.dumps(result,sort_keys=True,indent=2));sys.exit(bool(result['errors']))
