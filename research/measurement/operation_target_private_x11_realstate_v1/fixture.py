from __future__ import annotations
import argparse,json,os,time,tkinter as tk
from pathlib import Path

ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--session',type=int,required=True); args=ap.parse_args()
rootdir=Path(args.root); public=rootdir/'public'; oracle=rootdir/'oracle'; public.mkdir(parents=True); oracle.mkdir(parents=True)
cmdf=rootdir/'command.json'; ready=rootdir/'ready'; done=rootdir/'done'
app=tk.Tk(); app.title(f'ai-fixture-{args.session}'); app.geometry('320x240+0+0'); app.configure(bg='black')
cv=tk.Canvas(app,width=320,height=240,bg='black',highlightthickness=0); cv.pack(fill='both',expand=True)
text=cv.create_text(160,30,text='INIT',fill='white'); boxes=[]; last_seq=-1
COLORS={
 'CURRENT_CLICK_UNIQUE':'#008000','CURRENT_CLICK_MULTI':'#00a000','CURRENT_TYPE':'#0000ff','CURRENT_SCROLL_MULTI':'#0080ff',
 'NO_ACTION':'#666666','MISSING_TARGET':'#202020','AMBIGUOUS_TARGET':'#ffff00','STALE':'#ff0000','UNSUPPORTED_OPERATION':'#800080','PAYLOAD_MISSING':'#ff8000'}

def atom(path,obj):
    tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(obj,sort_keys=True)); os.replace(tmp,path)

def candidate(tid,role,op): return {'id':tid,'role':role,'ops':[op]}

def apply(seq,mode):
    global boxes
    applied=time.perf_counter_ns(); cv.configure(bg=COLORS[mode]); cv.itemconfig(text,text=mode)
    for b in boxes: cv.delete(b)
    boxes=[]
    sid=f's{args.session:02d}'; gen=seq+1
    allowed=['CLICK','TYPE_TEXT','SCROLL']; cands=[]; adm='CURRENT'; payload=None; acc=[]
    if mode=='CURRENT_CLICK_UNIQUE':
        cands=[candidate(f'{sid}-save','button','CLICK')]; acc=[{'op':'CLICK','target':cands[0]['id']}]
    elif mode=='CURRENT_CLICK_MULTI':
        cands=[candidate(f'{sid}-a','button','CLICK'),candidate(f'{sid}-b','button','CLICK')]; acc=[{'op':'CLICK','target':x['id']} for x in cands]
    elif mode=='CURRENT_TYPE':
        payload=f'payload-{sid}-{seq}'; cands=[candidate(f'{sid}-field','field','TYPE_TEXT')]; acc=[{'op':'TYPE_TEXT','target':cands[0]['id'],'payload_ref':payload}]
    elif mode=='CURRENT_SCROLL_MULTI':
        cands=[candidate(f'{sid}-pane1','scroll_region','SCROLL'),candidate(f'{sid}-pane2','scroll_region','SCROLL')]; acc=[{'op':'SCROLL','target':x['id']} for x in cands]
    elif mode=='NO_ACTION':
        adm='NOT_REQUIRED'; acc=[{'op':'NO_LOCAL_ACTION','reason':'ALREADY_SATISFIED'}]
    elif mode=='MISSING_TARGET':
        adm='MISSING'; acc=[{'op':'YIELD','reason':'MISSING_TARGET'}]
    elif mode=='AMBIGUOUS_TARGET':
        adm='AMBIGUOUS'; cands=[candidate(f'{sid}-x','button','CLICK'),candidate(f'{sid}-y','button','CLICK')]; acc=[{'op':'YIELD','reason':'AMBIGUOUS_TARGET'}]
    elif mode=='STALE':
        adm='STALE'; cands=[candidate(f'{sid}-stale','button','CLICK')]; acc=[{'op':'YIELD','reason':'STALE_STATE'}]
    elif mode=='UNSUPPORTED_OPERATION':
        adm='NOT_REQUIRED'; allowed=['CLICK','TYPE_TEXT']; acc=[{'op':'YIELD','reason':'UNSUPPORTED_OPERATION'}]
    elif mode=='PAYLOAD_MISSING':
        adm='CURRENT'; cands=[candidate(f'{sid}-field2','field','TYPE_TEXT')]; acc=[{'op':'YIELD','reason':'PAYLOAD_MISSING'}]
    else: raise ValueError(mode)
    for i,c in enumerate(cands):
        x=30+i*100; boxes.append(cv.create_rectangle(x,90,x+70,145,fill='white',outline='cyan'))
        boxes.append(cv.create_text(x+35,118,text=c['role'][:6],fill='black'))
    app.update_idletasks(); app.update()
    public_receipt={
      'session_id':sid,'observation_id':f'obs-{sid}-{gen}','generation':gen,'allowed_operations':allowed,
      'candidates':cands,'target_admissibility':adm,'payload_ref':payload,'receipt_ns':time.perf_counter_ns()
    }
    oracle_row={'session_id':sid,'generation':gen,'hidden_mode':mode,'acceptable':acc,'applied_ns':applied,'oracle_ns':time.perf_counter_ns(),'color':COLORS[mode]}
    atom(public/f'{seq:02d}.json',public_receipt); atom(oracle/f'{seq:02d}.json',oracle_row)

def poll():
    global last_seq
    if done.exists(): app.destroy(); return
    if cmdf.exists():
        try: cmd=json.loads(cmdf.read_text())
        except Exception: cmd=None
        if cmd and int(cmd['seq'])>last_seq:
            apply(int(cmd['seq']),cmd['mode']); last_seq=int(cmd['seq'])
    app.after(5,poll)
ready.write_text(str(time.perf_counter_ns())); app.after(5,poll); app.mainloop()
