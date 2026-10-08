"""Controlled private-X11 tests of pointer-only same-client focus equivalence."""
import argparse,hashlib,json,shutil,time
from pathlib import Path
from Xlib import X,XK
from session_v9 import suite
from input_owner_v6 import InputOwner
from lease import Lease
from executor_v3 import DecisionRequired
HERE=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    sources=[Path(__file__).resolve(),HERE/'input_owner_v6.py',HERE/'lease.py',HERE/'executor_v3.py']
    (a.out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
    s=suite.Session();d=s.d;root=d.screen().root;owner=None;rows=[]
    def window(parent,x,y,width,height):
        w=parent.create_window(x,y,width,height,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,override_redirect=True,background_pixel=0xffffff)
        w.map();d.sync();return w
    first=window(root,50,80,200,180);child=window(first,0,0,60,60);sibling=window(first,70,0,60,60);other=window(root,400,80,200,180)
    def focus(w):w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    def active(w):root.change_property(d.intern_atom('_NET_ACTIVE_WINDOW'),Xatom,32,[w.id]);d.sync()
    Xatom=d.intern_atom('WINDOW')
    def lease():
        l=Lease(time.perf_counter_ns()+2_000_000_000);l.expected_focus=child.id;l.expected_surface=first.id;l.expected_geometry=[50,80,200,180];return l
    def start():
        active(first);focus(child);l=lease();owner.call('move',l,{'x':80,'y':110});owner.call('button_down',l,1);return l
    def reject(name,fn):
        try:fn()
        except DecisionRequired:rows.append({'case':name,'rejected':True})
        else:raise AssertionError(name)
    def released(name,l):
        end=time.monotonic()+.5
        while root.query_pointer().mask & X.Button1Mask and time.monotonic()<end:time.sleep(.005)
        assert not root.query_pointer().mask & X.Button1Mask
        assert any(r.get('valid_until_ns')==l.deadline and r.get('verified') and r.get('reason')=='focus_changed' for r in owner.records)
        rows.append({'case':name,'released':True})
    try:
        owner=InputOwner(s.name)
        for target,name in [(first,'child_to_parent'),(sibling,'child_to_sibling')]:
            l=start();focus(target);time.sleep(.03);owner.call('move',l,{'x':90,'y':120});assert root.query_pointer().mask & X.Button1Mask
            rows.append({'case':name,'held_and_moved':True});owner.call('release',l)
        l=start();focus(first);reject('keyboard_does_not_inherit_pointer_equivalence',lambda:owner.call('down',l,'a'));owner.call('release',l)
        l=start();focus(other);released('foreign_focus',l)
        l=start();active(other);released('foreign_active_client_same_focus',l)
        active(first);focus(child);l=lease();owner.call('down',l,'a');owner.call('move',l,{'x':80,'y':110});owner.call('button_down',l,1);focus(first);released('mixed_keyboard_pointer_keeps_exact_focus',l)
        kc=d.keysym_to_keycode(XK.string_to_keysym('a'));assert not d.query_keymap()[kc//8] & (1<<(kc%8))
        active(first);focus(first);l=lease();l.expected_focus=other.id;reject('foreign_original_focus_not_rebound',lambda:owner.call('move',l,{'x':80,'y':110}))
        active(first);focus(child);l=lease();l.expected_geometry=[51,80,200,180];reject('geometry_still_required',lambda:owner.call('move',l,{'x':80,'y':110}))
    except Exception as e:rows.append({'error':repr(e)});raise
    finally:
        if owner:owner.close();(a.out/'owner-events.json').write_text(json.dumps(owner.records,indent=2)+'\n')
        s.close();shutil.rmtree(s.tmp);(a.out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows))
if __name__=='__main__':main()
