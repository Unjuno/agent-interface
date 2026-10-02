"""One owned private X11 allocation; actual public API input, no model benchmark."""
import json, pathlib, subprocess, time, sys
from unittest.mock import patch
from Xlib import X, display
from runtime.cli_v1 import api
from runtime.cli_v1.mcp_session import MCPSessionOwner
from runtime.core_v1.contract import SCHEMA_PROGRAM

out = pathlib.Path(sys.argv[1])
out.mkdir(exist_ok=False)
name = ':287'
rows = []
owner = None
client = None
with (out/'xvfb.stderr').open('w') as err:
    xvfb = subprocess.Popen(['Xvfb', name, '-screen', '0', '640x480x24', '-nolisten', 'tcp', '-nolisten', 'unix'], stderr=err, stdout=subprocess.DEVNULL)
    try:
        deadline = time.monotonic()+3
        while True:
            if xvfb.poll() is not None: raise RuntimeError('owned Xvfb exited before connection')
            try:
                client=display.Display(name)
                break
            except Exception:
                if time.monotonic()>deadline: raise
                time.sleep(.02)
        win=client.screen().root.create_window(40,40,320,160,0,client.screen().root_depth,X.InputOutput,X.CopyFromParent,background_pixel=client.screen().white_pixel,event_mask=X.KeyPressMask|X.KeyReleaseMask)
        win.set_wm_name('Owned public dispatch fixture')
        win.map(); client.sync()
        owner=MCPSessionOwner({'fixture':win.id},display_name=name)
        session=owner.get()
        original=api.dispatch_in_session
        original_release=session.backend.release_all
        releases=[]
        def tracked_release():
            row=original_release(); releases.append(row);return row
        session.backend.release_all=tracked_release
        def program(key, ident):
            return {'schema':SCHEMA_PROGRAM,'program_id':ident,'source':{'observation_seq':7,'binding_revision':1},'authority':{'lease_id':ident,'expires_at_ns':time.monotonic_ns()+2_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':[key]},{'op':'release_all'}]}
        first=owner.dispatch(program('a','normal'),current_observation_seq=7,current_binding_revision=1)
        rows.append({'case':'normal','report':first})
        if first.get('result',{}).get('status')!='completed': raise RuntimeError('normal input not completed')
        calls=[]
        def uncertain(*args,**kwargs):
            report=original(*args,**kwargs); calls.append(report)
            raise OSError('injected response loss after completed actual input')
        with patch.object(api,'dispatch_in_session',side_effect=uncertain):
            try:
                owner.dispatch(program('b','response-loss'),current_observation_seq=7,current_binding_revision=1)
            except OSError as e:
                rows.append({'case':'response_loss','error':repr(e),'actual_api_reports':calls})
            else: raise RuntimeError('response-loss injection absent')
        if len(calls)!=1 or calls[0].get('result',{}).get('status')!='completed': raise RuntimeError('uncertain input was not exactly one completed call')
        before=len(releases)
        close=owner.close(); again=owner.close()
        if len(releases)!=before+1 or close!=again or close['status']!='closed': raise RuntimeError('cleanup not one idempotent release')
        client.sync()
        events=[]
        while client.pending_events():
            event=client.next_event()
            if event.type in (X.KeyPress,X.KeyRelease): events.append({'type':event.type,'keycode':event.detail})
        expected=[{'type':kind,'keycode':client.keysym_to_keycode(ord(key))} for key in ['a','b'] for kind in [X.KeyPress,X.KeyRelease]]
        if events!=expected: raise RuntimeError('independent key event stream differs: '+repr(events))
        result={'status':'PASS','display':name,'window_id':win.id,'rows':rows,'independent_events':events,'expected_events':expected,'releases':releases,'close':close,'scope':'actual X11 input and cleanup mechanics; response-loss fault injected after completed input; not partial-held-input, GUI task scoring or latency/model comparison'}
    finally:
        if owner is not None: owner.close()
        if client is not None: client.close()
        xvfb.terminate()
        try: code=xvfb.wait(timeout=3)
        except subprocess.TimeoutExpired:
            xvfb.kill();code=xvfb.wait(timeout=3)
    result['xvfb_exit_code']=code
    (out/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'status':result['status'],'xvfb_exit_code':code,'independent_events':result['independent_events']}))
