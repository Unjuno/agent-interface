"""Fresh real window positions; fixed template and thresholds before capture."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
from PIL import Image,ImageGrab
from session_v16 import suite
from modal_visual_predicate_v2 import ModalVisualPredicate
HERE=Path(__file__).resolve().parent;out=HERE/'results/modal-translation-01';out.mkdir(exist_ok=False)
config=json.loads((HERE/'results/modal-predicate-01/config.json').read_text())
positions=[(440,250),(310,350)]
(out/'plan.json').write_text(json.dumps(dict(positions=positions,config=config,states=['excel','odf'],classification='FRESH_VARIANT; known family'),indent=2)+'\n')
template=HERE/'results/modal-focus-01/tab-0.png'
predicate=ModalVisualPredicate(Image.open(template).convert('RGB'),**config)
s=suite.Session();rows=[]
def geometry(window):
    g=window.get_geometry();pos=s.d.screen().root.translate_coords(window,0,0)
    return [pos.x,pos.y,g.width,g.height]
try:
    _,output,_=suite.prepare(s,'calc',991022,'unused');suite.base.CHAR_GAP_MS=0
    driver=suite.base.Driver(s,settle_ms=0)
    driver.text('532');driver.key('Return');driver.text('590');driver.key('Return');driver.chord('Control_L','s');time.sleep(.6)
    window=s.d.get_input_focus().focus;base=geometry(window)
    for index,(x,y) in enumerate(positions):
        subprocess.run(['wmctrl','-ir',hex(window.id),'-e',f'0,{x},{y},-1,-1'],env=s.env,check=True);time.sleep(.2)
        for focus in ('excel','odf'):
            if focus=='odf':driver.key('Tab');driver.key('Tab');time.sleep(.15)
            before=geometry(window);im=ImageGrab.grab(xdisplay=s.name).convert('RGB');after=geometry(window)
            assert before==after and before[2:]==base[2:]
            path=out/f'{index}-{focus}.png';im.save(path)
            offset=[before[0]-base[0],before[1]-base[1]]
            rows.append(dict(image=path.name,expected_focus=focus,base_geometry=base,geometry_before=before,geometry_after=after,offset=offset,
                             fixed=predicate.inspect(im),translated=predicate.inspect_at(im,offset)))
        driver.key('Tab');time.sleep(.15) # Restore Excel focus for next position.
    driver.key('Escape')
finally:
    if (s.tmp/'application.log').exists():shutil.copy2(s.tmp/'application.log',out/'application.txt')
    s.close();shutil.rmtree(s.tmp)
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
paths=[Path(__file__),HERE/'modal_visual_predicate.py',HERE/'modal_visual_predicate_v2.py',template,HERE/'results/modal-predicate-01/config.json']
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
print(json.dumps(rows,indent=2))
