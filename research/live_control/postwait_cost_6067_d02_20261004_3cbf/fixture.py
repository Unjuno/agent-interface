"""Fresh diagnostic source; ONLY post-draw-wait full snapshot varies."""
import argparse
import json
import os
import time
from pathlib import Path
from common import await_file,until,write
from x11 import X11
from timing import paced_wait,snapshot

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--display',required=True)
    ap.add_argument('--cell',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); spec=json.loads(a.cell.read_text()); root=a.out
    x=X11(a.display); w,gc=x.make_window(); events=[]; source_waits=[]
    trace=(root/'source.jsonl').open('x'); wait_log=(root/'source-waits.jsonl').open('x')
    def traced_wait(due,kind,identity):
        pre=snapshot(); waited=paced_wait(due); trial=None
        if kind=='draw':
            begin=time.monotonic_ns(); process_before=time.process_time_ns(); thread_before=time.thread_time_ns()
            post=snapshot() if spec['treatment']=='full' else None
            thread_after=time.thread_time_ns(); process_after=time.process_time_ns(); end=time.monotonic_ns()
            trial={'begin_ns':begin,'end_ns':end,'process_cpu_before_ns':process_before,
                   'process_cpu_after_ns':process_after,'thread_cpu_before_ns':thread_before,
                   'thread_cpu_after_ns':thread_after}
        else:
            post=snapshot()
        return {'kind':kind,'id':identity,'due_ns':due,'pre':pre,'wait':waited,'post':post,'trial':trial}
    def record(waited,start,end):
        waited.update(paint_start_ns=start,paint_end_ns=end); source_waits.append(waited)
        wait_log.write(json.dumps(waited,sort_keys=True)+'\n'); wait_log.flush()
    try:
        write(root/'fixture-ready.json',{'pid':os.getpid(),'window':w})
        epoch=await_file(root/'epoch.json')['epoch_ns']
        plan=([(i+1,120*i+12,120*i+22) for i in range(8)] if spec['kind']=='pulse'
              else [(1,-20,1000)] if spec['kind']=='persistent' else [])
        for identity,onset_ms,clear_ms in plan:
            color=0xFF0000 if identity%2 else 0x00FF00
            onset,clear=epoch+onset_ms*1_000_000,epoch+clear_ms*1_000_000
            draw_wait=traced_wait(onset,'draw',identity); start,end=x.paint(w,gc,identity,color)
            record(draw_wait,start,end)
            trace.write(json.dumps({'event':'draw','id':identity,'start':start,'end':end})+'\n'); trace.flush()
            clear_wait=traced_wait(clear,'clear',identity); cs,ce=x.paint(w,gc,0,0)
            record(clear_wait,cs,ce)
            trace.write(json.dumps({'event':'clear','id':identity,'start':cs,'end':ce})+'\n'); trace.flush()
            events.append({'id':identity,'color':color,'onset_ns':onset,'due_clear_ns':clear,
                           'draw_start_ns':start,'draw_end_ns':end,'clear_start_ns':cs,'clear_end_ns':ce})
        until(epoch+1_050_000_000)
        write(root/'source.json',{'pid':os.getpid(),'window':w,'epoch_ns':epoch,
                                 'treatment':spec['treatment'],'events':events,'wait_traces':source_waits,
                                 'final_pixels':x.capture(w)[3],'final_keymap':x.keymap()})
    finally:
        trace.close(); wait_log.close(); x.close()

if __name__=='__main__': main()
