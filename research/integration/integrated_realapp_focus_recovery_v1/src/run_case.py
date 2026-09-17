from __future__ import annotations
import hashlib, json, os, signal, subprocess, sys, time
from pathlib import Path
from Xlib import display
import adapter

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / 'test.svg'


def sh(cmd, env, timeout=5, check=True):
    return subprocess.run(cmd, env=env, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=timeout, check=check)


def wait_windows(env, timeout=10.0):
    end=time.time()+timeout
    last=''
    while time.time()<end:
        p=sh(['wmctrl','-lx'],env,check=False); last=p.stdout
        rows=[line for line in last.splitlines() if line.strip()]
        ink=next((r.split()[0] for r in rows if 'inkscape' in r.lower()),None)
        xt=next((r.split()[0] for r in rows if 'recovery862' in r.lower()),None)
        if ink and xt: return ink,xt,last
        time.sleep(.1)
    raise RuntimeError('windows_not_ready:'+last)


def window_context(d):
    root=d.screen().root
    focus=d.get_input_focus().focus
    if not hasattr(focus,'id'): raise RuntimeError('focus_not_window')
    chain=[]; w=focus; chosen=None
    for _ in range(16):
        try: cls=w.get_wm_class()
        except Exception: cls=None
        try: title=w.get_wm_name()
        except Exception: title=None
        row={'xid':int(w.id),'wm_class':list(cls) if cls else None,'title':title}
        chain.append(row)
        joined=' '.join(cls or ()).lower()
        if 'inkscape' in joined or 'recovery862' in joined or 'xterm' in joined:
            chosen=w; chosen_row=row; break
        try:
            parent=w.query_tree().parent
        except Exception:
            break
        if not hasattr(parent,'id') or parent.id==w.id: break
        w=parent
    if chosen is None:
        raise RuntimeError('client_not_resolved:'+json.dumps(chain))
    cls=' '.join(chosen_row.get('wm_class') or []).lower()
    role='A' if 'inkscape' in cls else ('B' if ('recovery862' in cls or 'xterm' in cls) else 'UNKNOWN')
    g=chosen.get_geometry()
    tr=chosen.translate_coords(root,0,0)
    geometry=[int(tr.x),int(tr.y),int(g.width),int(g.height)]
    return {'role':role,'raw_focus_xid':int(focus.id),'raw_surface_xid':int(chosen.id),
            'geometry':geometry,'chain':chain,'wm_class':chosen_row.get('wm_class'),'title':chosen_row.get('title')}


def input_state(d):
    km=d.query_keymap()
    pointer=d.screen().root.query_pointer()
    return {'key_bytes_nonzero':sum(1 for x in km if x), 'pointer_mask':int(pointer.mask)}


class Client:
    def __init__(self, d, arm, source_context):
        self.d=d; self.arm=arm; self.source_context=source_context
        self.submit_calls=[]; self.recovery_queries=0; self.real_x11_queries=0
        self.last_program=None; self.baseline_result=None; self.recovery_raw=None
    def check(self,*_a,**_k): return {'eligible':True}, {'noop':True}
    def submit(self,label,steps,timeout=10):
        self.submit_calls.append({'label':label,'steps':steps})
        self.last_program={'terminal':{'status':'rejected','reason':'focus_mismatch'},'steps':steps}
        return self.last_program
    def observe_only(self):
        self.recovery_queries += 1
        if self.arm=='retained_stale_context':
            raw=dict(self.source_context)
            receipt={'focus':'A','surface':'A','geometry':list(raw['geometry']),
                     'authority':'none','task_input_granted':False,'action_admission_eligible':False,
                     'evidence_role':'rejected_source_context',
                     'raw_focus_xid':raw['raw_focus_xid'],'raw_surface_xid':raw['raw_surface_xid']}
        elif self.arm=='real_observe_only':
            self.real_x11_queries += 1
            raw=window_context(self.d)
            receipt={'focus':raw['role'],'surface':raw['role'],'geometry':list(raw['geometry']),
                     'authority':'none','task_input_granted':False,'action_admission_eligible':False,
                     'evidence_role':'current_observation',
                     'raw_focus_xid':raw['raw_focus_xid'],'raw_surface_xid':raw['raw_surface_xid']}
        else: raise ValueError(self.arm)
        self.recovery_raw=raw
        return receipt


def terminate(p):
    if p is None: return
    try: p.terminate(); p.wait(timeout=2)
    except Exception:
        try: p.kill(); p.wait(timeout=2)
        except Exception: pass


def run(case_id, arm, display_no, out_path):
    case_dir=out_path.parent/case_id; case_dir.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy(); env['DISPLAY']=f':{display_no}'; env['XAUTHORITY']=str(case_dir/'Xauthority')
    Path(env['XAUTHORITY']).write_bytes(b'')
    old_display=os.environ.get('DISPLAY'); old_xauth=os.environ.get('XAUTHORITY')
    os.environ['DISPLAY']=env['DISPLAY']; os.environ['XAUTHORITY']=env['XAUTHORITY']
    procs=[]
    xvfb=subprocess.Popen(['Xvfb',env['DISPLAY'],'-screen','0','800x500x24','-nolisten','tcp','-ac'],env=env,
                          stdout=(case_dir/'xvfb.out').open('w'),stderr=subprocess.STDOUT)
    procs.append(xvfb); time.sleep(.25)
    openbox=subprocess.Popen(['openbox'],env=env,stdout=(case_dir/'openbox.out').open('w'),stderr=subprocess.STDOUT)
    procs.append(openbox); time.sleep(.4)
    ink=subprocess.Popen(['inkscape',str(SVG)],env=env,stdout=(case_dir/'inkscape.out').open('w'),stderr=subprocess.STDOUT)
    xt=subprocess.Popen(['xterm','-name','recovery862','-T','Recovery-B-862','-e','sh','-c','sleep 9999'],env=env,
                        stdout=(case_dir/'xterm.out').open('w'),stderr=subprocess.STDOUT)
    procs.extend([ink,xt])
    try:
        ink_id,xt_id,wm=wait_windows(env)
        sh(['wmctrl','-ia',ink_id],env); time.sleep(.18)
        d=display.Display(env['DISPLAY'])
        source=window_context(d); source_input=input_state(d)
        if source['role']!='A': raise RuntimeError('source_not_A')
        sh(['wmctrl','-ia',xt_id],env); time.sleep(.18)
        admission=window_context(d); admission_input=input_state(d)
        if admission['role']!='B': raise RuntimeError('admission_not_B')
        before=window_context(d); before_input=input_state(d)
        client=Client(d,arm,source)
        pinned_execute=adapter.execute_handles
        def traced(c,task,aliases):
            z=pinned_execute(c,task,aliases); c.baseline_result=z; return z
        adapter.execute_handles=traced
        status='ok'; rejection=None; composed=None
        try:
            composed=adapter.execute_with_policy(client,{'task_id':case_id,'token':'never-sent'},
                                                 {'field':'field','submit':'submit'},'focus_recovery_adapter')
        except adapter.RecoveryRejected as e:
            status='recovery_rejected'; rejection=str(e)
        finally:
            adapter.execute_handles=pinned_execute
        after=window_context(d); after_input=input_state(d)
        d.close()
        result={
            'case_id':case_id,'arm':arm,'status':status,'recovery_rejection':rejection,
            'source':source,'admission':admission,'pre_recovery_actual':before,'post_recovery_actual':after,
            'source_input':source_input,'admission_input':admission_input,'pre_input':before_input,'post_input':after_input,
            'baseline_result':client.baseline_result,'last_terminal':client.last_program['terminal'] if client.last_program else None,
            'composed':composed,'submit_count_total':len(client.submit_calls),
            'post_rejection_task_submits':0 if composed is None else composed['post_rejection_task_submits'],
            'recovery_queries':client.recovery_queries,'real_x11_queries':client.real_x11_queries,
            'recovery_raw':client.recovery_raw,'svg_sha256':hashlib.sha256(SVG.read_bytes()).hexdigest(),
            'wmctrl':wm,'setup_ids':{'inkscape':ink_id,'xterm':xt_id},
        }
        out_path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        return result
    finally:
        for p in reversed(procs): terminate(p)
        if old_display is None: os.environ.pop('DISPLAY',None)
        else: os.environ['DISPLAY']=old_display
        if old_xauth is None: os.environ.pop('XAUTHORITY',None)
        else: os.environ['XAUTHORITY']=old_xauth

if __name__=='__main__':
    run(sys.argv[1],sys.argv[2],int(sys.argv[3]),Path(sys.argv[4]))
