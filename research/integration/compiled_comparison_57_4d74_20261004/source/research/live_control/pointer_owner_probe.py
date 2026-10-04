"""Real X11 primitive probe. No shared backend integration or agent task claim."""
import argparse,hashlib,json,sys,time
from pathlib import Path
from Xlib import X
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_gating'))
from gui_suite import Session
from input_owner_v3 import InputOwner
from lease import Lease,Expired
from executor_v3 import Cancelled,DecisionRequired

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    sources=[Path(__file__).resolve(),HERE/'input_owner_v3.py',HERE/'lease.py',HERE/'executor_v3.py']
    (a.out/'manifest.json').write_text(json.dumps({'scope':'private X11 primitive correctness, not runtime qualification','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}},indent=2)+'\n')
    s=Session();d=s.d;root=d.screen().root;owner=None;rows=[]
    def window(x,y):
        w=root.create_window(x,y,200,180,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,override_redirect=True,background_pixel=0xffffff,event_mask=X.ButtonPressMask|X.ButtonReleaseMask|X.PointerMotionMask)
        w.map();d.sync();return w
    first=window(50,80);second=window(400,80)
    first.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    def lease(ms=1000):
        l=Lease(time.perf_counter_ns()+ms*1_000_000);l.expected_focus=first.id;l.expected_surface=first.id;return l
    def reject(label,fn,kind):
        try:fn()
        except kind:rows.append({'case':label,'rejected':True})
        else:raise AssertionError(label+' accepted')
    def released(label,l,reason):
        time.sleep(.06)
        mask=root.query_pointer().mask
        assert not mask & X.Button1Mask,label
        assert any(r['reason']==reason and r['verified'] for r in owner.records),label
        rows.append({'case':label,'button1_down':False,'release_reason':reason})
    try:
        owner=InputOwner(s.name)
        l=lease();owner.call('move',l,{'x':100,'y':120});owner.call('button_down',l,1)
        assert root.query_pointer().mask & X.Button1Mask
        owner.call('move',l,{'x':180,'y':180});owner.call('button_up',l,1);owner.call('wheel',l,2);owner.call('release',l)
        events=[]
        d.sync()
        while d.pending_events():
            e=d.next_event()
            if e.type in (X.ButtonPress,X.ButtonRelease):events.append([e.type,e.detail])
        assert [X.ButtonPress,1] in events and [X.ButtonRelease,1] in events
        assert events.count([X.ButtonPress,4])==2 and events.count([X.ButtonRelease,4])==2
        rows.append({'case':'move_drag_vertical_wheel','events':events,'pointer':[root.query_pointer().root_x,root.query_pointer().root_y]})
        l=lease(-1);reject('expired_move',lambda:owner.call('move',l,{'x':110,'y':120}),Expired)
        l=lease();l.set();reject('cancelled_press',lambda:owner.call('button_down',l,1),Cancelled)
        l=lease();reject('other_surface',lambda:owner.call('move',l,{'x':450,'y':120}),DecisionRequired)
        l=lease();reject('out_of_root',lambda:owner.call('move',l,{'x':-1,'y':10}),ValueError)
        l=lease(35);owner.call('button_down',l,1);released('deadline_release_without_worker_calls',l,'expired')
        l=lease();owner.call('button_down',l,1);l.set();released('cancel_release_without_worker_calls',l,'cancelled')
        l=lease();owner.call('button_down',l,1);second.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();released('focus_release',l,'focus_changed')
        first.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
        l=lease();owner.call('button_down',l,1);cover=window(60,90);released('same_focus_overlay_release',l,'surface_changed');cover.destroy();d.sync()
        newer=lease();owner.call('button_down',newer,1)
        reject('old_lease_cannot_release_new_button',lambda:owner.call('button_up',l,1),ValueError)
        assert root.query_pointer().mask & X.Button1Mask
        owner.call('release',newer)
        # Existing keyboard path remains usable in this same owner.
        l=lease();owner.call('down',l,'a');owner.call('up',l,'a');owner.call('release',l)
        rows.append({'case':'keyboard_regression','passed':True})
    finally:
        if owner:
            owner.close();(a.out/'owner-events.json').write_text(json.dumps(owner.records,indent=2)+'\n')
        s.close()
        for p in s.procs:p.wait(timeout=5)
        import shutil
        shutil.rmtree(s.tmp)
        (a.out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({'checks':len(rows),'passed':True}))

if __name__=='__main__':main()
