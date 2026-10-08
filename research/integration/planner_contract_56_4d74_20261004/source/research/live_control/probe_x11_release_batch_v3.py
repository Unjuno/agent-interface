"""Development-only Xvfb probe for v3 release ordering and post-batch cost."""
from __future__ import annotations
import argparse, json, queue, statistics, threading, time
from Xlib import X, XK, display
from Xlib.ext import xtest


def pct(values, q):
    s=sorted(values); x=(len(s)-1)*q; lo=int(x); hi=min(lo+1,len(s)-1); f=x-lo
    return int(round(s[lo]*(1-f)+s[hi]*f))


def stats(values):
    return {'min':min(values),'median':int(statistics.median(values)),'p95':pct(values,.95),'p99':pct(values,.99),'max':max(values)}


class Owner:
    def __init__(self, display_name):
        self.q=queue.Queue(); self.ready=threading.Event(); self.ops=[]
        self.thread=threading.Thread(target=self._run,args=(display_name,),daemon=True); self.thread.start()
        if not self.ready.wait(2): raise RuntimeError('owner start timeout')
        if hasattr(self,'error'): raise self.error
    def call(self,op,key=None):
        done=threading.Event(); reply=[]; self.q.put((op,key,done,reply))
        if not done.wait(2): raise RuntimeError('owner reply timeout')
        ok,val=reply[0]
        if not ok: raise val
        return val
    def _run(self,name):
        try:d=display.Display(name)
        except Exception as exc:self.error=exc;self.ready.set();return
        held=set(); self.ready.set()
        while True:
            op,key,done,reply=self.q.get()
            try:
                self.ops.append((op,key,time.perf_counter_ns()))
                if op=='close': val=None
                elif op=='down':
                    code=d.keysym_to_keycode(XK.string_to_keysym(key)); held.add(code)
                    xtest.fake_input(d,X.KeyPress,code); d.sync(); val={'code':code}
                elif op=='up':
                    code=d.keysym_to_keycode(XK.string_to_keysym(key))
                    if code in held:
                        xtest.fake_input(d,X.KeyRelease,code); d.sync(); held.remove(code)
                    val=None
                elif op=='input_state':
                    st=time.perf_counter_ns(); val={'owner_id':'probe-owner','owned_keycodes':sorted(held),'sample_started_ns':st,'sample_finished_ns':time.perf_counter_ns()}
                else: raise ValueError(op)
                reply.append((True,val))
            except Exception as exc: reply.append((False,exc))
            finally: done.set()
            if op=='close': break
        d.close()
    def close(self): self.call('close'); self.thread.join(2)


def physical_down(d,code):
    m=d.query_keymap(); return bool(m[code//8] & (1<<(code%8)))


def receipt(owner,key,deadline):
    start=time.perf_counter_ns()
    ordinary=start < deadline
    owner.call('up',key)
    end=time.perf_counter_ns()
    return {'event':'input_release_transition','key':key,'owner_id':'probe-owner','intent_token':'intent-1',
            'release_call_started_ns':start,'release_call_returned_ns':end,'ordinary_release_candidate':ordinary}


def run_batch(owner, verifier, codes, keys):
    for k in keys: owner.call('down',k)
    down=all(physical_down(verifier,codes[k]) for k in keys)
    start_ops=len(owner.ops); deadline=time.perf_counter_ns()+2_000_000_000
    rows=[]; gaps=[]; prev_return=None
    for k in keys:
        if prev_return is not None:
            local_start=time.perf_counter_ns(); gaps.append(local_start-prev_return)
        row=receipt(owner,k,deadline); rows.append(row); prev_return=row['release_call_returned_ns']
    post_start=time.perf_counter_ns(); state=owner.call('input_state'); post_return=time.perf_counter_ns()
    emitted=[]
    latest=max(r['release_call_returned_ns'] for r in rows)
    verified=(state['owned_keycodes']==[] and state['sample_started_ns']>=latest and all(r['ordinary_release_candidate'] for r in rows))
    for pos,r in enumerate(rows):
        emitted.append({**r,'release_batch_position':pos,'release_batch_size':len(rows),'owner_transition_verified':verified})
    up=state['owned_keycodes']==[] and not any(physical_down(verifier,codes[k]) for k in keys)
    ops=[op for op,_,_ in owner.ops[start_ops:]]
    expected=['up']*len(keys)+['input_state']
    return {
        'down':down,'up':up,'order':ops==expected,'rows':emitted,
        'release_windows':[r['release_call_returned_ns']-r['release_call_started_ns'] for r in rows],
        'gaps':gaps,'batch_window':rows[-1]['release_call_returned_ns']-rows[0]['release_call_started_ns'],
        'post_sample_delay':post_return-rows[-1]['release_call_returned_ns'],
        'post_sample_call_delay':post_return-post_start,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--display',required=True); ap.add_argument('--trials',type=int,default=500); ap.add_argument('--out')
    a=ap.parse_args(); owner=Owner(a.display); verifier=display.Display(a.display)
    codes={k:verifier.keysym_to_keycode(XK.string_to_keysym(k)) for k in ('a','d')}
    summary={}
    try:
        for label,keys in [('single',['a']),('two_key',['a','d'])]:
            downs=ups=orders=verified=0; windows=[];gaps=[];batch=[];post=[];postcall=[]
            for _ in range(a.trials):
                r=run_batch(owner,verifier,codes,keys)
                downs+=r['down']; ups+=r['up']; orders+=r['order']; verified+=all(x['owner_transition_verified'] for x in r['rows'])
                windows.extend(r['release_windows']);gaps.extend(r['gaps']);batch.append(r['batch_window']);post.append(r['post_sample_delay']);postcall.append(r['post_sample_call_delay'])
            summary[label]={
                'trials':a.trials,'physical_down_verified':downs,'physical_up_verified':ups,'exact_operation_order':orders,'verified_telemetry_batches':verified,
                'release_call_window_ns':stats(windows),'batch_window_ns':stats(batch),'post_final_release_sample_and_publish_delay_ns':stats(post),
                'input_state_call_ns':stats(postcall),
            }
            if gaps: summary[label]['between_release_local_gap_ns']=stats(gaps)
        result={'schema':'x11-release-batch-v3-probe','display':a.display,'batches':summary,
                'pass':all(v['physical_down_verified']==a.trials and v['physical_up_verified']==a.trials and v['exact_operation_order']==a.trials and v['verified_telemetry_batches']==a.trials for v in summary.values()),
                'interpretation':'development Xvfb only; validates single/two-key ordering and post-final-release instrumentation timing, not MAP01 latency'}
        text=json.dumps(result,indent=2)+"\n"; print(text,end='')
        if a.out: open(a.out,'w').write(text)
    finally:
        for k in ('a','d'):
            try: owner.call('up',k)
            except Exception: pass
        owner.close();verifier.close()

if __name__=='__main__': main()
