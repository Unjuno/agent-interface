"""Controlled private X11 continuation admission; not planner/path replacement."""
import argparse,hashlib,json,shutil,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from Xlib import X
from Xlib.ext import xtest
from session_v9 import suite
from input_owner_v8 import InputOwner
from lease import Lease
from executor_v3 import DecisionRequired
HERE=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    paths=[Path(__file__).resolve(),HERE/'input_owner_v8.py',HERE/'lease.py',HERE/'executor_v3.py']
    (a.out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
    s=suite.Session();d=s.d;root=d.screen().root;owner=None;rows=[];retired=[]
    def window(x):
        w=root.create_window(x,80,200,180,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,override_redirect=True,background_pixel=0xffffff);w.map();d.sync();return w
    first=window(50);other=window(400)
    def focus(w):
        root.change_property(d.intern_atom('_NET_ACTIVE_WINDOW'),d.intern_atom('WINDOW'),32,[w.id]);w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    def start(ms=2000):
        focus(first);l=Lease(time.perf_counter_ns()+ms*1_000_000);l.expected_focus=first.id;l.expected_surface=first.id;l.expected_geometry=[50,80,200,180]
        owner.call('move',l,{'x':100,'y':120});owner.call('button_down',l,1);return l,owner.call('input_state')
    def payload(state,x=130):return {'owner_id':state['owner_id'],'expected_revision':state['revision'],'x':x,'y':120}
    def reject(name,l,state):
        before=root.query_pointer()
        try:owner.call('continue_move',l,payload(state))
        except (ValueError,DecisionRequired):pass
        else:raise AssertionError(name)
        after=root.query_pointer();assert (before.root_x,before.root_y)==(after.root_x,after.root_y)
        rows.append({'case':name,'rejected_without_motion':True})
    try:
        owner=InputOwner(s.name);l,state=start();deadline=l.deadline
        result=owner.call('continue_move',l,payload(state));assert result['continuation'] and result['revision']>state['revision']
        assert root.query_pointer().root_x==130 and root.query_pointer().mask & X.Button1Mask and l.deadline==deadline
        rows.append({'case':'valid_continuation','same_lease_and_hold':True});reject('duplicate_reply',l,state);owner.call('release',l)
        l,state=start();owner.call('move',l,{'x':110,'y':120});reject('intervening_input',l,state);owner.call('release',l)
        l,state=start();owner.call('release',l);reject('after_release',l,state)
        l,state=start();xtest.fake_input(d,X.ButtonRelease,1);d.sync();reject('external_physical_release',l,state);owner.call('release',l)
        l,state=start(60);time.sleep(.1);reject('after_expiry',l,state);assert not root.query_pointer().mask & X.Button1Mask
        l,state=start();l.set();time.sleep(.02);reject('after_cancel',l,state)
        l,state=start();focus(other);time.sleep(.02);reject('foreign_surface',l,state)
        l,state=start();owner.call('down',l,'a');state=owner.call('input_state');reject('mixed_keyboard_hold',l,state);owner.call('release',l)
        l,state=start();first.configure(x=60);d.sync();reject('changed_geometry',l,state);owner.call('release',l);first.configure(x=50);d.sync()
        l,state=start()
        def contender(x):
            try:return owner.call('continue_move',l,payload(state,x))
            except ValueError:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(contender,[140,150]))
        assert sum(r is not None for r in results)==1
        rows.append({'case':'concurrent_duplicate_revision','admitted':1});owner.call('release',l)
        l,state=start();owner.close();retired=owner.records;owner=InputOwner(s.name);newlease,newstate=start()
        forged=dict(newstate,owner_id=state['owner_id']);reject('prior_owner_same_current_revision',newlease,forged);owner.call('release',newlease)
    except Exception as e:rows.append({'error':repr(e)});raise
    finally:
        if owner:owner.close();(a.out/'owner-events.json').write_text(json.dumps({'retired':retired,'current':owner.records},indent=2)+'\n')
        s.close();(a.out/'cleanup.json').write_text(json.dumps({'all_owned_processes_exited':all(p.poll() is not None for p in s.procs)})+'\n');shutil.rmtree(s.tmp)
        (a.out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows))
if __name__=='__main__':main()
