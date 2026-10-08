from pathlib import Path
import json,hashlib
from host_image_custody import verify_local_images
root=Path(__file__).resolve().parent;out=root/'host-custody-01';out.mkdir(exist_ok=False);image=out/'probe.png';image.write_bytes((root/'fixture-input/source.png').read_bytes())
r={'relative_path':'probe.png','host_path':str(image),'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'bytes':image.stat().st_size}
(out/'image-path-receipts.jsonl').write_text(json.dumps(r)+'\n');msg={'method':'turn/start','params':{'input':[{'type':'localImage','path':str(image)}]}}
positive=verify_local_images(msg,out);controls={}
image.write_bytes(image.read_bytes()+b'x')
try:verify_local_images(msg,out);controls['changed_bytes']=False
except ValueError:controls['changed_bytes']=True
try:verify_local_images({'method':'turn/start','params':{'input':[{'type':'localImage','path':str(root/'fixture-input/source.png')}]}},out);controls['outside_root']=False
except ValueError:controls['outside_root']=True
image.write_bytes((root/'fixture-input/source.png').read_bytes());(out/'image-path-receipts.jsonl').write_text('')
try:verify_local_images(msg,out);controls['missing_receipt']=False
except ValueError:controls['missing_receipt']=True
result={'scope':'saved-file host gate construction only; zero provider/game/input calls','positive':positive,'rejected':controls};(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert all(controls.values())
