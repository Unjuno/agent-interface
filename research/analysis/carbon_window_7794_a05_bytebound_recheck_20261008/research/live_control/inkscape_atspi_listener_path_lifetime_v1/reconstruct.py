#!/usr/bin/env python3
import hashlib,json,tarfile
from pathlib import Path
r=Path(__file__).resolve().parent;m=json.loads((r/"manifest.json").read_text());p=r/m["archive"]["path"];b=p.read_bytes();assert len(b)==m["archive"]["bytes"] and hashlib.sha256(b).hexdigest()==m["archive"]["sha256"];o=r/"reconstructed";o.mkdir(exist_ok=True);tarfile.open(p,"r:gz").extractall(o);print({"ok":True,"sha256":m["archive"]["sha256"]})
