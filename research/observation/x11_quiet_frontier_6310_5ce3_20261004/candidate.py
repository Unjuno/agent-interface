"""One native focus-frontier allocation; no keyboard/pointer/model emissions."""
import argparse,datetime,hashlib,json,os,select,subprocess,time,uuid
from pathlib import Path
from Xlib import X,display
from policy import classify
ROOT=Path(__file__).parent
def query(d):
    t=time.monotonic_ns();r=d.get_input_focus()
    return {'start_ns':t,'end_ns':time.monotonic_ns(),'focus':getattr(r.focus,'id',r.focus),'revert_to':r.revert_to}
def drain(d):
    events=[]
    while d.pending_events():
        e=d.next_event()
        events.append({'type':e.type,'window':getattr(getattr(e,'window',None),'id',None),
                       'detail':getattr(e,'detail',None),'mode':getattr(e,'mode',None),
                       'sequence':getattr(e,'sequence_number',None),'send_event':bool(getattr(e,'send_event',False))})
    return events
def set_focus(d,w,label,history):
    t=time.monotonic_ns();w.set_input_focus(X.RevertToNone,X.CurrentTime)
    witness=query(d)
    assert witness['focus']==w.id,('focus assignment failed',label,witness)
    history.append({'label':label,'request_ns':t,'witness':witness})
def cell(out,index,context,repeat):
    r={'index':index,'context':context,'repeat':repeat,'epoch':uuid.uuid4().hex,'error':None,
       'keyboard_pointer_emissions':0,'history':[],'cleanup':{}}
    clients=[];proc=None;log=None
    try:
        log=(out/('xvfb_%02d.stderr'%index)).open('xb')
        proc=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','160x100x24','-nolisten','tcp','-noreset'],stdout=subprocess.PIPE,stderr=log)
        assert select.select([proc.stdout],[],[],5)[0],'Xvfb display timeout'
        name=':'+proc.stdout.readline().decode().strip();r['display']=name;r['xvfb_pid']=proc.pid
        owner=display.Display(name);observer=display.Display(name);mutator=display.Display(name)
        clients=[owner,observer,mutator];root=owner.screen().root
        windows=[root.create_window(10+70*i,10,50,50,0,owner.screen().root_depth,X.InputOutput,X.CopyFromParent,background_pixel=owner.screen().white_pixel,override_redirect=True)for i in range(2)]
        for win in windows:win.map()
        owner.sync();r['windows']=[w.id for w in windows]
        r['viewable']=[[w.get_attributes().map_state for w in windows]for _ in range(2)]
        assert r['viewable']==[[X.IsViewable]*2]*2,'nonviewable source'
        watched=[observer.create_resource_object('window',w.id)for w in windows]
        targets=[mutator.create_resource_object('window',w.id)for w in windows]
        for win in watched:win.change_attributes(event_mask=X.FocusChangeMask)
        observer.sync()
        set_focus(mutator,targets[0],'setup_A',r['history']);observer.sync();drain(observer)
        for target,label in [(targets[1],'qualify_B'),(targets[0],'qualify_A')]:set_focus(mutator,target,label,r['history'])
        r['qualification_barrier']=query(observer);r['qualification_events']=drain(observer)
        assert [e['type']for e in r['qualification_events']]==[X.FocusOut,X.FocusIn,X.FocusOut,X.FocusIn],'unqualified subscription'
        covered=context!='unsubscribed_aba'
        if not covered:
            for win in watched:win.change_attributes(event_mask=0)
            observer.sync();drain(observer)
        r['subscription']={'covered':covered,'mask':X.FocusChangeMask if covered else 0,'windows':r['windows'],'epoch':r['epoch']}
        r['A']=query(observer);assert r['A']['focus']==windows[0].id
        assert drain(observer)==[],'dirty starting prefix'
        r['consumer_journal_at_A']=[]
        r['pre_frontier_history_start']=len(r['history'])
        if context in ('aba','unsubscribed_aba'):
            set_focus(mutator,targets[1],'before_F_B',r['history']);set_focus(mutator,targets[0],'before_F_A',r['history'])
        elif context=='persistent_change':set_focus(mutator,targets[1],'before_F_B',r['history'])
        # No consumer queue read between A and F: explicitly stale local journal.
        r['naive_silence_quiet']=not r['consumer_journal_at_A']
        r['source_before_F']=query(mutator)
        r['F']=query(observer);r['events_through_F']=drain(observer)
        r['endpoint_equality_quiet']=r['A']['focus']==r['F']['focus']
        r['generation_result']=classify(covered,True,r['events_through_F'])
        r['after_frontier_history_start']=len(r['history'])
        if context=='change_after_frontier':set_focus(mutator,targets[1],'after_F_B',r['history'])
        r['B']=query(mutator);r['post_B_barrier']=query(observer);r['events_after_F']=drain(observer)
        r['safe_to_act_at_B']=False
        # Cleanup is not task input; leave owned display's focus at PointerRoot.
        mutator.set_input_focus(X.PointerRoot,X.RevertToNone,X.CurrentTime)
        r['cleanup']['focus']=query(mutator)
        r['cleanup']['keymap']=bytes(observer.query_keymap()).hex()
        mask=observer.screen().root.query_pointer().mask
        r['cleanup']['observed_buttons123']=mask&(X.Button1Mask|X.Button2Mask|X.Button3Mask)
        assert r['cleanup']['focus']['focus']==X.PointerRoot
        assert not any(bytes.fromhex(r['cleanup']['keymap']))and r['cleanup']['observed_buttons123']==0
        for win in windows:win.destroy()
        owner.sync();r['cleanup']['windows_destroyed']=True
    except Exception as e:r['error']=repr(e)
    finally:
        for d in reversed(clients):
            try:d.close()
            except Exception as e:r['cleanup'].setdefault('errors',[]).append(repr(e))
        r['cleanup']['connections_closed']=len(clients)
        if proc is not None:
            proc.terminate()
            try:code=proc.wait(timeout=3)
            except subprocess.TimeoutExpired:proc.kill();code=proc.wait(timeout=3);r['cleanup']['xvfb_killed_after_timeout']=True
            r['cleanup']['xvfb_exit']=code
            proc.stdout.close()
        if log:log.close()
    return r
def main():
    parser=argparse.ArgumentParser();parser.add_argument('out');parser.add_argument('--preflight',action='store_true');a=parser.parse_args()
    out=Path(a.out);out.mkdir(exist_ok=True)
    plan=json.loads((ROOT/'PLAN.json').read_text());rows=[]
    contexts=['quiet']if a.preflight else plan['contexts'];repeats=1 if a.preflight else plan['repeats']
    with(out/'raw.jsonl').open('x')as f:
        for repeat in range(repeats):
            for context in contexts:
                r=cell(out,len(rows),context,repeat);rows.append(r);f.write(json.dumps(r,sort_keys=True)+'\n');f.flush()
                if r['error']is not None:
                    print(json.dumps({'status':'STOP_NATIVE_SOURCE','row':r['index'],'error':r['error']}));raise SystemExit(1)
    env={'python':os.sys.version,'candidate_pid':os.getpid(),'started_scope':'preflight'if a.preflight else'formal','rows':len(rows),
         'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip(),'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
         'pids_max':Path('/sys/fs/cgroup/pids.max').read_text().strip(),'memory_swap_max':Path('/sys/fs/cgroup/memory.swap.max').read_text().strip()}
    with(out/'ENVIRONMENT.json').open('x')as f:json.dump(env,f,indent=2)
    print(json.dumps({'status':'NATIVE_ROWS_RETAINED','rows':len(rows)}))
if __name__=='__main__':main()
