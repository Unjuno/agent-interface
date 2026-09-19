"""Development-only Xvfb probe for two-key batched release instrumentation."""
from __future__ import annotations
import argparse, json, queue, statistics, threading, time
from Xlib import X, XK, display
from Xlib.ext import xtest


def percentile(values, q):
    ordered=sorted(values)
    if not ordered:return None
    i=(len(ordered)-1)*q
    lo=int(i); hi=min(lo+1,len(ordered)-1); frac=i-lo
    return int(round(ordered[lo]*(1-frac)+ordered[hi]*frac))


class Owner:
    def __init__(self, display_name):
        self.q=queue.Queue(); self.ready=threading.Event(); self.thread=threading.Thread(target=self.run,daemon=True)
        self.display_name=display_name; self.ops=[]; self.thread.start()
        if not self.ready.wait(2): raise RuntimeError('owner start timeout')
        if hasattr(self,'error'): raise self.error
    def call(self,op,key=None):
        done=threading.Event(); reply=[]; self.q.put((op,key,done,reply))
        if not done.wait(2): raise RuntimeError('owner reply timeout')
        ok,value=reply[0]
        if not ok: raise value
        return value
    def run(self):
        try:d=display.Display(self.display_name)
        except Exception as exc:self.error=exc;self.ready.set();return
        held=set(); self.d=d; self.ready.set()
        while True:
            op,key,done,reply=self.q.get()
            try:
                self.ops.append((op,key,time.perf_counter_ns()))
                if op=='close': result=None
                elif op=='down':
                    code=d.keysym_to_keycode(XK.string_to_keysym(key)); held.add(code)
                    xtest.fake_input(d,X.KeyPress,code);d.sync();result={'code':code}
                elif op=='up':
                    code=d.keysym_to_keycode(XK.string_to_keysym(key))
                    if code in held:
                        xtest.fake_input(d,X.KeyRelease,code);d.sync();held.remove(code)
                    result=None
                elif op=='input_state':
                    started=time.perf_counter_ns(); result={'sample_started_ns':started,'owned_keycodes':sorted(held),'sample_finished_ns':time.perf_counter_ns()}
                else: raise ValueError(op)
                reply.append((True,result))
            except Exception as exc:reply.append((False,exc))
            finally:done.set()
            if op=='close':break
        d.close()
    def close(self):self.call('close');self.thread.join(2)


def physical_down(d, code):
    bitmap=d.query_keymap(); return bool(bitmap[code//8] & (1<<(code%8)))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--display',required=True);ap.add_argument('--trials',type=int,default=500);ap.add_argument('--out')
    args=ap.parse_args(); owner=Owner(args.display); verifier=display.Display(args.display)
    codes={k:verifier.keysym_to_keycode(XK.string_to_keysym(k)) for k in ('a','d')}
    release_windows=[]; inter_release_gaps=[]; post_batch_delays=[]; batch_windows=[]
    both_down=both_up=sample_order_ok=0
    try:
        for _ in range(args.trials):
            owner.call('down','a');owner.call('down','d')
            if all(physical_down(verifier,codes[k]) for k in ('a','d')): both_down+=1
            op_start=len(owner.ops)
            s1=time.perf_counter_ns();owner.call('up','a');r1=time.perf_counter_ns()
            receipt1=(s1,r1)
            s2=time.perf_counter_ns();owner.call('up','d');r2=time.perf_counter_ns()
            receipt2=(s2,r2)
            sample_call_started=time.perf_counter_ns();state=owner.call('input_state');sample_returned=time.perf_counter_ns()
            ops=[op for op,_,_ in owner.ops[op_start:]]
            if ops==['up','up','input_state']:sample_order_ok+=1
            if state['owned_keycodes']==[] and not any(physical_down(verifier,codes[k]) for k in ('a','d')):both_up+=1
            release_windows.extend([r1-s1,r2-s2]);inter_release_gaps.append(s2-r1)
            post_batch_delays.append(sample_returned-r2);batch_windows.append(r2-s1)
        result={
            'schema':'x11-release-batch-v2-probe', 'trials':args.trials,
            'two_keys':['a','d'], 'both_down_verified':both_down, 'both_up_verified':both_up,
            'exact_operation_order_trials':sample_order_ok,
            'release_call_window_ns':{'min':min(release_windows),'median':int(statistics.median(release_windows)),'p95':percentile(release_windows,.95),'p99':percentile(release_windows,.99),'max':max(release_windows)},
            'between_release_local_gap_ns':{'min':min(inter_release_gaps),'median':int(statistics.median(inter_release_gaps)),'p95':percentile(inter_release_gaps,.95),'p99':percentile(inter_release_gaps,.99),'max':max(inter_release_gaps)},
            'two_release_batch_window_ns':{'min':min(batch_windows),'median':int(statistics.median(batch_windows)),'p95':percentile(batch_windows,.95),'p99':percentile(batch_windows,.99),'max':max(batch_windows)},
            'post_batch_input_state_delay_ns':{'min':min(post_batch_delays),'median':int(statistics.median(post_batch_delays)),'p95':percentile(post_batch_delays,.95),'p99':percentile(post_batch_delays,.99),'max':max(post_batch_delays)},
            'pass': both_down==args.trials and both_up==args.trials and sample_order_ok==args.trials,
            'interpretation':'development Xvfb probe only; validates no owner-state sample between two explicit releases and measures post-batch instrumentation delay'
        }
        text=json.dumps(result,indent=2)+"\n"; print(text,end='')
        if args.out:open(args.out,'w').write(text)
    finally:
        try: owner.call('up','a')
        except Exception: pass
        try: owner.call('up','d')
        except Exception: pass
        owner.close();verifier.close()

if __name__=='__main__':main()
