import hashlib
import json
from pathlib import Path
import platform
import sys
import time
from datetime import datetime, timezone
root=Path(__file__).parent
raw=root/'raw'
files=[]
for path in sorted(raw.iterdir()):
    if path.is_file():
        data=path.read_bytes()
        files.append({'name':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(root/'RAW-SHA256.json').write_text(json.dumps({'algorithm':'sha256','files':files},indent=2,sort_keys=True)+'\n',encoding='utf-8')
(root/'HOST-READBACK.json').write_text(json.dumps({'captured_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'implementation':platform.python_implementation(),'test_host':'local Windows shell; no WSLc or Docker session'},indent=2,sort_keys=True)+'\n',encoding='utf-8')
