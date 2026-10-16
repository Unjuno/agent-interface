"""Setup-only real UI focus variants; no runtime policy or oracle control."""
import hashlib,json,shutil,time
from pathlib import Path
from PIL import ImageGrab
from session_v16 import suite
HERE=Path(__file__).resolve().parent;out=HERE/'results/modal-focus-01';out.mkdir(exist_ok=False)
s=suite.Session();rows=[]
try:
    goal,output,_=suite.prepare(s,'calc',991022,'unused')
    suite.base.CHAR_GAP_MS=0
    driver=suite.base.Driver(s,settle_ms=0)
    driver.text('532');driver.key('Return');driver.text('590');driver.key('Return');driver.chord('Control_L','s');time.sleep(.6)
    for i in range(4):
        if i:driver.key('Tab');time.sleep(.15)
        im=ImageGrab.grab(xdisplay=s.name).convert('RGB');im.save(out/f'tab-{i}.png')
        rows.append(dict(tab_count=i,focus=s.d.get_input_focus().focus.id,windows=s.windows(),image=f'tab-{i}.png'))
    driver.key('Escape')
finally:
    if (s.tmp/'application.log').exists():shutil.copy2(s.tmp/'application.log',out/'application.txt')
    s.close();shutil.rmtree(s.tmp)
(out/'states.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE.parent/'observation_gating/gui_suite.py',HERE.parent/'real_apps_v1/real_app_suite_v1.py')},indent=2)+'\n')
print(json.dumps(rows))
