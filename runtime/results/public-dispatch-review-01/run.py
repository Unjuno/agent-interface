import json, os, subprocess, sys, hashlib, socket, time
from PIL import Image
from pathlib import Path
from Xlib import X, display
out=Path('results-local/public-dispatch-review-live-01').resolve()
out.mkdir(exist_ok=False)
number='147'
assert not Path('/tmp/.X11-unix/X'+number).exists()
assert not Path('/tmp/.X'+number+'-lock').exists()
assert ('@/tmp/.X11-unix/X'+number) not in Path('/proc/net/unix').read_text()
server=subprocess.Popen(['Xvfb',':'+number,'-screen','0','640x480x24','-nolisten','tcp','-nolisten','unix'],stdout=subprocess.DEVNULL,stderr=(out/'xvfb.stderr.log').open('wb'))
d=None
try:
    for _ in range(100):
        if server.poll() is not None: raise RuntimeError('owned Xvfb exited')
        if ('@/tmp/.X11-unix/X'+number) in Path('/proc/net/unix').read_text(): break
        time.sleep(.05)
    else: raise RuntimeError('owned Xvfb readiness timeout')
    name=':'+number
    d=display.Display(name)
    screen=d.screen()
    assert (screen.width_in_pixels,screen.height_in_pixels)==(640,480)
    window=screen.root.create_window(40,40,400,180,0,screen.root_depth,X.InputOutput,X.CopyFromParent,background_pixel=0x16324f)
    window.set_wm_name('Agent Interface public observation integration')
    window.map(); d.sync()
    gc=window.create_gc(foreground=0xffffff)
    window.draw_text(gc,20,45,'Public CLI observation -> review')
    gc.change(foreground=0x39d98a)
    window.fill_rectangle(gc,20,75,180,45)
    d.sync()
    raw_before=bytes(window.get_image(0,0,400,180,X.ZPixmap,0xFFFFFFFF).data)
    Image.frombytes('RGB',(400,180),raw_before,'raw','BGRX').save(out/'direct-before.png')
    targets=out/'targets.json';targets.write_text(json.dumps({'fixture':window.id}))
    report=out/'observation.json'
    from runtime.core_v1.contract import SCHEMA_PROGRAM
    program={'schema':SCHEMA_PROGRAM,'program_id':'two-captures',
        'source':{'observation_seq':0,'binding_revision':0},
        'authority':{'lease_id':'owned-fixture','expires_at_ns':time.monotonic_ns()+5_000_000_000},
        'terminal':{'release_all_required':True},
        'ops':[{'op':'focus','target':'fixture'},
               {'op':'observe','frame':'window_client','x':0,'y':0,'w':400,'h':180},
               {'op':'observe','frame':'window_client','x':20,'y':75,'w':180,'h':45},
               {'op':'release_all'}]}
    program_path=out/'program.json';program_path.write_text(json.dumps(program))
    observed=subprocess.run([sys.executable,'-m','runtime.cli_v1','dispatch','--program',str(program_path),'--targets',str(targets),'--current-observation-seq','0','--current-binding-revision','0','--capture-directory',str(out/'images'),'--display',name],capture_output=True)
    report.write_bytes(observed.stdout)
    if observed.returncode: raise RuntimeError(observed.stderr.decode()+observed.stdout.decode())
    raw_after=bytes(window.get_image(0,0,400,180,X.ZPixmap,0xFFFFFFFF).data)
    Image.frombytes('RGB',(400,180),raw_after,'raw','BGRX').save(out/'direct-after.png')
    reviewed=subprocess.run([sys.executable,'-m','runtime.cli_v1','review','--report',str(report),'--run-directory',str(out)],capture_output=True)
    (out/'review.json').write_bytes(reviewed.stdout)
    row=json.loads(reviewed.stdout)
    if reviewed.returncode: raise RuntimeError(str(row))
    captures=json.loads(observed.stdout)['result']['execution']['observations']
    assert len(captures)==2
    assert row['image_reference']['execution_observation_index']==1
    assert row['image_reference']['sha256']==captures[-1]['artifact']['sha256']
    (out/'comparison.json').write_text(json.dumps({'captures':len(captures),'selected_index':1,'selected_hash_matches':True,'selected_dimensions':[captures[-1]['width'],captures[-1]['height']]}))
    print(json.dumps({'status':row['image_status'],'reference':row['image_reference'],'execution_status':row['receipt']['report']['result']['status']}))
finally:
    if d is not None:d.close()
    server.terminate()
    server.communicate(timeout=10)
