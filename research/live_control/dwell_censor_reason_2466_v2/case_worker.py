import argparse, json, os, pathlib, subprocess, sys, time, tkinter as tk

def ns(): return time.monotonic_ns()
def ms(a,b): return (b-a)/1e6

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--family',choices=['TK_CALLBACK','WORKER_FILE'],required=True)
    ap.add_argument('--scenario',required=True)
    ap.add_argument('--policy',choices=['GENERIC_CENSOR','CAUSE_AWARE'],required=True)
    ap.add_argument('--rep',type=int,required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    out=pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=False)
    if a.family=='TK_CALLBACK':
        horizon_ms=100; finite_M_ms=250; censor_at_ms=70
        effect_table={'NORMAL':40,'HORIZON_LATE':160,'FOCUS_LOSS':160,'OWNER_DEATH':160,'BOUND_VIOLATION':330,'UNKNOWN_BOUND':160}
    else:
        horizon_ms=550; finite_M_ms=850; censor_at_ms=300
        effect_table={'NORMAL':50,'HORIZON_LATE':250,'FOCUS_LOSS':250,'OWNER_DEATH':250,'BOUND_VIOLATION':650,'UNKNOWN_BOUND':250}
    M_ms=None if a.scenario=='UNKNOWN_BOUND' else finite_M_ms
    effect_ms=effect_table[a.scenario]
    censor_ms=censor_at_ms if a.scenario in ('FOCUS_LOSS','OWNER_DEATH') else None
    events=[]; worker=None; effect_file=out/'worker_effect.txt'
    root=tk.Tk(); root.geometry('360x160+0+0'); root.title('dwell-censor-fixture')
    target=tk.Toplevel(root); target.geometry('240x120+20+20'); target.title('target-owner')
    status=tk.Label(target,text='PENDING',name='status'); status.pack()
    entry=tk.Entry(target,name='target_entry'); entry.pack(); entry.insert(0,'target')
    other=tk.Entry(root,name='other_entry'); other.pack(); other.insert(0,'other')
    root.update(); entry.focus_force(); root.update()
    start=ns()
    events.append({'type':'ready','t_ns':start,'focus':str(root.focus_get()),'owner_alive':bool(target.winfo_exists())})
    state={'effect_done':False,'effect_ns':None,'owner_alive':True,'focus_target':True,'censor_reason':None}

    def complete_effect(source):
        if state['owner_alive'] and target.winfo_exists():
            status.config(text='DONE'); state['effect_done']=True; state['effect_ns']=ns()
            events.append({'type':'effect','source':source,'t_ns':state['effect_ns']})
        else:
            events.append({'type':'effect_after_owner_death','source':source,'t_ns':ns()})

    if a.family=='TK_CALLBACK':
        root.after(effect_ms, lambda: complete_effect('tk_after'))
    else:
        code="import pathlib,time,sys; time.sleep(float(sys.argv[1])/1000); pathlib.Path(sys.argv[2]).write_text('done',encoding='utf-8')"
        worker=subprocess.Popen([sys.executable,'-c',code,str(effect_ms),str(effect_file)])
        def poll_file():
            if effect_file.exists(): complete_effect('worker_file')
            elif root.winfo_exists(): root.after(5,poll_file)
        root.after(5,poll_file)

    if a.scenario=='FOCUS_LOSS':
        def lose_focus():
            other.focus_force(); root.update_idletasks(); state['focus_target']=False; state['censor_reason']='FOCUS_LOSS'
            events.append({'type':'focus_loss','t_ns':ns(),'focus':str(root.focus_get())})
        root.after(censor_ms,lose_focus)
    elif a.scenario=='OWNER_DEATH':
        def kill_owner():
            state['owner_alive']=False; state['censor_reason']='OWNER_DEATH'
            if target.winfo_exists(): target.destroy()
            events.append({'type':'owner_death','t_ns':ns()})
        root.after(censor_ms,kill_owner)

    def snapshot(label):
        alive=bool(state['owner_alive'] and target.winfo_exists())
        focus=str(root.focus_get()) if root.winfo_exists() else ''
        focus_target=alive and focus.endswith('target_entry')
        done=bool(state['effect_done'] and alive and status.cget('text')=='DONE') if alive else False
        rec={'label':label,'t_ns':ns(),'elapsed_ms':ms(start,ns()),'effect_done':done,'owner_alive':alive,'focus_target':focus_target,'focus':focus}
        events.append({'type':'snapshot',**rec}); return rec

    # Service the real GUI until the observation horizon.
    while ms(start,ns()) < horizon_ms:
        root.update(); time.sleep(0.002)
    h=snapshot('horizon')
    reason=state['censor_reason'] or ('COMPLETED' if h['effect_done'] else 'HORIZON')
    typed={'status':'COMPLETED' if h['effect_done'] else 'CENSORED','reason':reason,'horizon_ms':horizon_ms,'M_ms':M_ms,'clock':'CLOCK_MONOTONIC','family':a.family,'session':f'{a.family}-{a.scenario}-{a.rep}'}

    action='HOLD'; action_reason=''
    if h['effect_done'] and h['owner_alive'] and h['focus_target']:
        action='PROCEED'; action_reason='COMPLETED_AT_HORIZON'
    elif a.policy=='CAUSE_AWARE':
        if reason in ('FOCUS_LOSS','OWNER_DEATH'):
            action='HOLD'; action_reason=reason
        elif M_ms is None:
            action='HOLD'; action_reason='UNKNOWN_BOUND'
        else:
            while ms(start,ns()) < M_ms:
                root.update(); time.sleep(0.002)
            m=snapshot('M')
            if m['effect_done'] and m['owner_alive'] and m['focus_target']:
                action='PROCEED'; action_reason='REOBSERVED_COMPLETE_BEFORE_M'
            else:
                action='HOLD'; action_reason='BOUND_VIOLATED_OR_STATE_INVALID'
    else:
        # Deliberately weak comparator: collapse all censor causes to one horizon/M rule.
        if M_ms is None:
            action='PROCEED'; action_reason='HORIZON_AS_COMPLETION_WITHOUT_BOUND'
        else:
            while ms(start,ns()) < M_ms:
                root.update(); time.sleep(0.002)
            m=snapshot('M')
            action='PROCEED'; action_reason='GENERIC_BOUND_ASSUMED'

    pre_action=snapshot('pre_action')
    safe_precondition=pre_action['effect_done'] and pre_action['owner_alive'] and pre_action['focus_target']
    task_effect=False
    if action=='PROCEED' and pre_action['owner_alive']:
        # Application-like next-step effect; independent audit decides whether it was justified.
        try:
            if target.winfo_exists():
                status.config(text='NEXT'); task_effect=True; root.update_idletasks()
        except tk.TclError:
            task_effect=False
    events.append({'type':'decision','t_ns':ns(),'action':action,'action_reason':action_reason,'safe_precondition':safe_precondition,'task_effect':task_effect})
    final=snapshot('final')
    if worker is not None:
        try: worker.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            worker.kill(); worker.wait()
    try:
        if root.winfo_exists(): root.destroy()
    except tk.TclError: pass
    result={
      'family':a.family,'scenario':a.scenario,'policy':a.policy,'rep':a.rep,
      'horizon_ms':horizon_ms,'M_ms':M_ms,'effect_ms':effect_ms,
      'typed_receipt':typed,'action':action,'action_reason':action_reason,
      'safe_precondition':safe_precondition,'task_effect':task_effect,
      'unsafe_proceed': bool(action=='PROCEED' and not safe_precondition),
      'events':events,'worker_returncode':None if worker is None else worker.returncode,
      'pid':os.getpid()
    }
    (out/'result.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('family','scenario','policy','rep','action','unsafe_proceed')},sort_keys=True))
if __name__=='__main__': main()
