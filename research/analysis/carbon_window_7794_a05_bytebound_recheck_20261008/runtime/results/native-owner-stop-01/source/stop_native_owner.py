import hashlib,json,os,signal,shutil,time,sys
from pathlib import Path
import xml.etree.ElementTree as ET
from Xlib import display

p=Path(sys.argv[1])
meta=json.loads((p/'private-session.json').read_text())
checkpoint=json.loads((p/'before-reply.json').read_text())
owner=meta['owner']
assert owner==checkpoint['owner']
row=Path(f"/proc/{owner['pid']}/stat").read_text()
fields=row[row.rfind(')')+2:].split()
assert fields[19]==owner['starttime'] and fields[0]=='T'
assert not (p/'reply-1.json').exists()
result={'checkpoint':checkpoint['phase'],'owner':owner,'before_kill_state':fields[0],
        'kill_requested_ns':time.monotonic_ns()}
os.kill(owner['pid'],signal.SIGKILL)
for _ in range(100):
    try:
        row=Path(f"/proc/{owner['pid']}/stat").read_text()
        fields=row[row.rfind(')')+2:].split()
        if fields[0]=='Z': break
    except FileNotFoundError:
        break
    time.sleep(.01)
else:
    raise RuntimeError('owner has not become terminal')
result['owner_terminal_observed_ns']=time.monotonic_ns()
d=display.Display(meta['display'])
result['independent_x11']={'keys_down':[i*8+b for i,v in enumerate(d.query_keymap()) for b in range(8) if v & (1<<b)],
    'pointer_mask':d.screen().root.query_pointer().mask,'known_ns':time.monotonic_ns()}
d.close()
src=Path(json.loads((p/'live-output.json').read_text())['path'])
shutil.copyfile(src,p/'independent-shape.svg')
result['saved_svg_sha256']=hashlib.sha256((p/'independent-shape.svg').read_bytes()).hexdigest()
result['saved_rect']=ET.parse(p/'independent-shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect').attrib
result['reply_exists']=(p/'reply-1.json').exists()
(p/'external-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
