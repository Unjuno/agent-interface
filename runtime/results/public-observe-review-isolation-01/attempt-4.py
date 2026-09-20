import json, os, subprocess, sys, hashlib
from PIL import Image
from pathlib import Path
from Xlib import X, display
out=Path('results-local/public-observe-review-live-04').resolve()
out.mkdir(exist_ok=False)
r,w=os.pipe()
server=subprocess.Popen(['Xvfb','-displayfd',str(w),'-screen','0','640x480x24','-nolisten','tcp','-nolisten','unix'],pass_fds=(w,),stdout=subprocess.DEVNULL,stderr=(out/'xvfb.stderr.log').open('wb'))
os.close(w)
d=None
try:
    with os.fdopen(r) as pipe: number=pipe.readline().strip()
    if not number: raise RuntimeError('Xvfb did not allocate a display')
    name=':'+number
    d=display.Display(name)
    screen=d.screen()
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
    observed=subprocess.run([sys.executable,'-m','runtime.cli_v1','observe','--targets',str(targets),'--target','fixture','--frame','window_client','--region','0','0','400','180','--capture-directory',str(out/'images'),'--display',name],capture_output=True)
    report.write_bytes(observed.stdout)
    if observed.returncode: raise RuntimeError(observed.stderr.decode()+observed.stdout.decode())
    raw_after=bytes(window.get_image(0,0,400,180,X.ZPixmap,0xFFFFFFFF).data)
    Image.frombytes('RGB',(400,180),raw_after,'raw','BGRX').save(out/'direct-after.png')
    (out/'comparison.json').write_text(json.dumps({'before_sha256':hashlib.sha256(raw_before).hexdigest(),'after_sha256':hashlib.sha256(raw_after).hexdigest(),'capture_sha256':json.loads(observed.stdout)['observation']['sha256'],'before_colors':len(set(Image.open(out/'direct-before.png').getdata())),'after_colors':len(set(Image.open(out/'direct-after.png').getdata()))}))
    reviewed=subprocess.run([sys.executable,'-m','runtime.cli_v1','review','--report',str(report),'--run-directory',str(out)],capture_output=True)
    (out/'review.json').write_bytes(reviewed.stdout)
    row=json.loads(reviewed.stdout)
    if reviewed.returncode: raise RuntimeError(str(row))
    print(json.dumps({'status':row['image_status'],'reference':row['image_reference'],'input_dispatched':row['receipt']['report']['input_dispatched']}))
finally:
    if d is not None:d.close()
    server.terminate()
    server.communicate(timeout=10)
