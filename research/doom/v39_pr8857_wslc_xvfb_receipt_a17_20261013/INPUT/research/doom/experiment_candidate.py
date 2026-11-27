"""Single-key actual-Xvfb construction for PR #8857 receipt integration."""
import json, os, select, subprocess, sys, time, traceback
from pathlib import Path
from Xlib import X, XK, display

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))
from input_owner_v10 import InputOwner as InputOwnerV10
from input_transition_owner_v3 import InputOwner as ReceiptOwner
from lease import Lease
from analyze_map01_direct_retained_input_v2 import analyze

OUT = Path('/out/raw.json')

def event_until(d, expected, timeout=2.0):
    end = time.monotonic() + timeout
    found = []
    while time.monotonic() < end:
        if d.pending_events():
            ev = d.next_event()
            if ev.type in (X.KeyPress, X.KeyRelease):
                found.append({'type': ev.type, 'detail': ev.detail,
                              'window': getattr(ev, 'event', None).id,
                              'observed_ns': time.perf_counter_ns()})
                if ev.type == expected:
                    return found
            continue
        ready, _, _ = select.select([d.fileno()], [], [], max(0, end-time.monotonic()))
        if not ready:
            break
    raise TimeoutError(f'expected X11 event {expected}; observed={found!r}')

def key_down(d, code):
    bitmap = d.query_keymap()
    return bool(bitmap[code // 8] & (1 << (code % 8)))

def main():
    raw = {'schema':'pr8857-wslc-xvfb-receipt-a17-raw-v1',
           'scope':'one w key down/up through PR #8857 V3 wrapper over real V10 owner on private Xvfb',
           'xvfb':{}, 'client_events':[], 'keymap':{}, 'admission':None,
           'release_transition':None, 'owner_records':[], 'owner_cleanup':None,
           'analyzer':None, 'error':None}
    xvfb = subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1024x768x24','-ac','-nolisten','tcp'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    owner = None
    client = None
    try:
        ready, _, _ = select.select([xvfb.stdout], [], [], 5)
        if not ready: raise TimeoutError('Xvfb displayfd timeout')
        display_no = xvfb.stdout.readline().strip()
        if not display_no.isdigit(): raise RuntimeError(f'invalid Xvfb displayfd value: {display_no!r}')
        display_name = ':' + display_no
        os.environ['DISPLAY'] = display_name
        raw['xvfb'] = {'display':display_name,'pid':xvfb.pid}
        client = display.Display(display_name)
        screen = client.screen()
        window = screen.root.create_window(20,20,320,160,0,screen.root_depth,
             X.InputOutput,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
        window.map(); client.sync(); window.set_input_focus(X.RevertToParent, X.CurrentTime); client.sync()
        focus = client.get_input_focus().focus
        focus_id = focus.id if hasattr(focus,'id') else focus
        if focus_id != window.id: raise RuntimeError(f'focus mismatch {focus_id} != {window.id}')
        raw['client_window'] = window.id
        raw['focus'] = focus_id
        class BoundLease(Lease):
            pass
        lease = BoundLease(time.perf_counter_ns()+10_000_000_000)
        lease.intent_token='a17-one-shot'
        lease.expected_focus=window.id
        lease.focus_invalid=False
        owner = ReceiptOwner(display_name, _owner_cls=InputOwnerV10)
        admission = owner.call('down', lease, 'w')
        raw['admission'] = admission
        code = client.keysym_to_keycode(XK.string_to_keysym('w'))
        if not code: raise RuntimeError('X server has no keycode for lowercase w')
        raw['keycode'] = code
        raw['client_events'].extend(event_until(client, X.KeyPress))
        raw['keymap']['while_held'] = key_down(client, code)
        release = owner.call('up', lease, 'w')
        raw['release_transition'] = release
        raw['client_events'].extend(event_until(client, X.KeyRelease))
        raw['keymap']['after_explicit_up'] = key_down(client, code)
        raw['owner_records'] = owner.records
        raw['analyzer'] = analyze([admission, release])
        owner.close()
        raw['owner_cleanup'] = {'closed':owner._inner.closed,'stopped':owner._inner.stopped.is_set(),
                                'thread_alive':owner._inner.thread.is_alive(),
                                'records':owner.records}
    except BaseException as exc:
        raw['error'] = {'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    finally:
        if owner is not None and not owner._inner.closed:
            try: owner.close()
            except BaseException as exc:
                raw['cleanup_error']={'type':type(exc).__name__,'message':str(exc)}
        if client is not None: client.close()
        if xvfb.poll() is None:
            xvfb.terminate()
        try: raw['xvfb']['exit'] = xvfb.wait(timeout=3)
        except subprocess.TimeoutExpired:
            xvfb.kill(); raw['xvfb']['exit'] = xvfb.wait()
        raw['xvfb']['stderr'] = xvfb.stderr.read()
        OUT.write_text(json.dumps(raw, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps({'raw':str(OUT),'error':raw['error'],
                      'event_types':[e['type'] for e in raw['client_events']],
                      'keymap':raw['keymap'],
                      'transition_owner_verified':(raw['release_transition'] or {}).get('owner_transition_verified'),
                      'analyzer_ready':(raw['analyzer'] or {}).get('measurement_ready'),
                      'xvfb_exit':raw['xvfb'].get('exit')}, sort_keys=True))

if __name__=='__main__': main()


