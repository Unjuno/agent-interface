from __future__ import annotations
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path

SKEW_NS=2_000_000
ARMS=('STABLE','DELAYED_PAINT','STALE_FOCUS','IDENTITY_MISMATCH')

def candidate(row):
    fs=row['fields']; ids=[(fs[k]['session'],fs[k]['surface'],fs[k]['generation']) for k in ('focus','target_binding','image','ui_context')]
    if len(set(ids))!=1: return False
    ts=[fs[k]['sample_ns'] for k in fs]
    if any(type(x) is not int for x in ts): return False
    anchor=max(ts)
    if anchor>row['now_ns']: return False
    if fs['focus']['valid_through_ns']<anchor or fs['target_binding']['valid_through_ns']<anchor: return False
    if anchor-fs['image']['sample_ns']>SKEW_NS or anchor-fs['ui_context']['sample_ns']>SKEW_NS: return False
    return True

def naive(row):
    fs=row['fields']; ids=[(fs[k]['session'],fs[k]['surface'],fs[k]['generation']) for k in ('focus','target_binding','image','ui_context')]
    if len(set(ids))!=1: return False
    ts=[fs[k]['sample_ns'] for k in fs]
    return max(ts)-min(ts)<=SKEW_NS

def strict(row):
    if not candidate(row): return False
    return len({row['fields'][k]['sample_ns'] for k in row['fields']})==1

def geom_tuple(w):
    g=w.get_geometry(); return (g.x,g.y,g.width,g.height,g.border_width,g.depth)

def set_focus(d,w):
    from Xlib import X
    w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()

def focus_id(d): return int(d.get_input_focus().focus.id)

def sample_row(arm, idx, d, xa, xb, root, canvas, rect, paint_state):
    session='x11-r2'; surface=str(xa.id); generation=1
    set_focus(d,xa); root.update()
    init_focus=focus_id(d); t_focus=time.perf_counter_ns()
    init_geom=geom_tuple(xa); t_geom=time.perf_counter_ns()

    if arm=='DELAYED_PAINT':
        paint_state[0]=1-paint_state[0]
        canvas.itemconfigure(rect, fill=('green' if paint_state[0] else 'red'))
        root.update_idletasks(); root.update()
    elif arm=='STALE_FOCUS':
        set_focus(d,xb); root.update()

    img=xa.get_image(20,20,16,16,2,0xFFFFFFFF)
    raw=img.data.encode('latin1') if isinstance(img.data,str) else bytes(img.data)
    t_img=time.perf_counter_ns()
    title=xa.get_wm_name() or ''
    t_ui=time.perf_counter_ns()
    anchor=max(t_focus,t_geom,t_img,t_ui)

    final_focus=focus_id(d); final_geom=geom_tuple(xa); t_reval=time.perf_counter_ns()
    focus_same=(final_focus==init_focus)
    geom_same=(final_geom==init_geom)
    focus_valid=anchor if focus_same else t_focus
    geom_valid=anchor if geom_same else t_geom

    fields={
      'focus':{'session':session,'surface':surface,'generation':generation,'sample_ns':t_focus,'value':init_focus,'valid_through_ns':focus_valid},
      'target_binding':{'session':session,'surface':surface,'generation':generation,'sample_ns':t_geom,'value':init_geom,'valid_through_ns':geom_valid},
      'image':{'session':session,'surface':surface,'generation':generation,'sample_ns':t_img,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},
      'ui_context':{'session':session,'surface':surface,'generation':generation,'sample_ns':t_ui,'title':title},
    }
    if arm=='IDENTITY_MISMATCH': fields['image']['generation']=2
    row={'arm':arm,'index':idx,'now_ns':t_reval,'fields':fields,
         'raw':{'initial_focus':init_focus,'final_focus':final_focus,'initial_geometry':init_geom,'final_geometry':final_geom,
                'revalidation_ns':t_reval,'image_bytes':len(raw)},
         'candidate':None,'naive':None,'strict':None,'oracle':None}
    row['candidate']=candidate(row); row['naive']=naive(row); row['strict']=strict(row)
    ids=[(fields[k]['session'],fields[k]['surface'],fields[k]['generation']) for k in fields]
    span=max(fields[k]['sample_ns'] for k in fields)-min(fields[k]['sample_ns'] for k in fields)
    nc_anchor=max(fields[k]['sample_ns'] for k in fields)
    nc_ok=(nc_anchor-fields['image']['sample_ns']<=SKEW_NS and nc_anchor-fields['ui_context']['sample_ns']<=SKEW_NS)
    row['oracle']=(len(set(ids))==1 and focus_same and geom_same and nc_ok)
    row['sample_span_ns']=span
    row['noncritical_age_max_ns']=max(nc_anchor-fields['image']['sample_ns'],nc_anchor-fields['ui_context']['sample_ns'])
    set_focus(d,xa); root.update()
    row['restored_focus']=focus_id(d)
    return row

def execute(rows_per_arm, display_num):
    auth=str(Path(__file__).with_name('empty.Xauthority')); Path(auth).touch(); os.environ['XAUTHORITY']=auth
    xvfb=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0','400x260x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    time.sleep(.15); os.environ['DISPLAY']=f':{display_num}'
    import tkinter as tk
    from Xlib import display
    root=tk.Tk(); root.title('EPOCH_A'); root.geometry('180x160+10+10')
    canvas=tk.Canvas(root,width=140,height=100,bg='black',highlightthickness=0); canvas.pack(padx=10,pady=10)
    rect=canvas.create_rectangle(10,10,80,60,fill='red',outline='')
    b=tk.Toplevel(root); b.title('EPOCH_B'); b.geometry('180x160+205+10'); tk.Label(b,text='B').pack()
    root.update(); time.sleep(.05); root.update()
    d=display.Display(); xa=d.create_resource_object('window',root.winfo_id()); xb=d.create_resource_object('window',b.winfo_id())
    paint_state=[0]; rows=[]
    try:
      for i in range(rows_per_arm*len(ARMS)):
        arm=ARMS[i%4]; rows.append(sample_row(arm,i,d,xa,xb,root,canvas,rect,paint_state))
      final_focus=focus_id(d)
    finally:
      try: d.close()
      except Exception: pass
      try: root.destroy()
      except Exception: pass
      xvfb.terminate()
      try: xvfb.wait(timeout=2)
      except Exception: xvfb.kill(); xvfb.wait()
    m={
      'rows':len(rows),'candidate_oracle_mismatch':sum(r['candidate']!=r['oracle'] for r in rows),
      'valid_stable_paint_joins':sum(r['candidate'] for r in rows if r['arm'] in ('STABLE','DELAYED_PAINT')),
      'strict_stable_paint_joins':sum(r['strict'] for r in rows if r['arm'] in ('STABLE','DELAYED_PAINT')),
      'candidate_stale_focus_joins':sum(r['candidate'] for r in rows if r['arm']=='STALE_FOCUS'),
      'naive_stale_focus_joins':sum(r['naive'] for r in rows if r['arm']=='STALE_FOCUS'),
      'candidate_identity_mismatch_joins':sum(r['candidate'] for r in rows if r['arm']=='IDENTITY_MISMATCH'),
      'max_sample_span_ns':max(r['sample_span_ns'] for r in rows),
      'stable_paint_within_2ms':sum(r['sample_span_ns']<=SKEW_NS for r in rows if r['arm'] in ('STABLE','DELAYED_PAINT')),
      'stale_focus_within_2ms':sum(r['sample_span_ns']<=SKEW_NS for r in rows if r['arm']=='STALE_FOCUS'),
      'restored_focus_all':all(r['restored_focus']==r['raw']['initial_focus'] for r in rows),
      'image_bytes_all_1024':all(r['raw']['image_bytes']==1024 for r in rows),
      'arm_counts':{a:sum(r['arm']==a for r in rows) for a in ARMS}
    }
    eligible=(m['candidate_oracle_mismatch']==0 and m['valid_stable_paint_joins']>0 and m['candidate_stale_focus_joins']==0 and m['naive_stale_focus_joins']>0 and m['candidate_identity_mismatch_joins']==0 and m['restored_focus_all'] and m['image_bytes_all_1024'])
    phase='formal' if rows_per_arm==64 else 'construction'
    if eligible:
      if phase=='formal' and (m['valid_stable_paint_joins']<96 or not (m['strict_stable_paint_joins']<m['valid_stable_paint_joins'])):
        decision='HOLD_X11_2MS_TRANSFER_NOT_EXPOSED'
      else:
        decision='PASS_OBSERVATION_EPOCH_BOUNDED_SKEW_X11_R2_SCOPED' if phase=='formal' else 'PASS_CONSTRUCTION_ELIGIBLE'
    else:
      if m['candidate_stale_focus_joins']>0: decision='FAIL_X11_CRITICAL_SKEW_LEAK'
      elif m['candidate_oracle_mismatch']>0 or m['candidate_identity_mismatch_joins']>0: decision='FAIL_X11_EPOCH_INTEGRITY'
      else: decision='HOLD_X11_2MS_TRANSFER_NOT_EXPOSED'
    return {'task':'OBSERVATION-EPOCH-BOUNDED-SKEW-X11-R2-20260918-001','phase':phase,'formal_invocations':1 if phase=='formal' else 0,'reruns':0,'replacements':0,'tuning':0,'decision':decision,'metrics':m,'rows':rows}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--rows-per-arm',type=int,default=8); ap.add_argument('--display',type=int,default=940); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=execute(a.rows_per_arm,a.display); Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps({'decision':r['decision'],'metrics':r['metrics']},indent=2,sort_keys=True))
if __name__=='__main__': main()
