from pathlib import Path
import subprocess,hashlib,json
root=Path(__file__).resolve().parent; repo=Path("C:/Users/junny/Documents/Codex/2026-09-19/new-chat/work/calc-construction-publication-4d74"); git="C:/Program Files/Git/cmd/git.exe"; base="a2f6b60ac84300d45beb82c7cf5a6e06cfc7c456"
out=root/"fixture-input";out.mkdir(exist_ok=False)
record={"base":base,"scope":"read-only setup materialization; not allocation reuse or game invocation","members":{}}
for name in ("fixture.json","save.png","source.png"):
 path="research/doom/fixtures/map01-threat-contact-v2/"+name
 data=subprocess.run([git,"show",base+":"+path],cwd=repo,check=True,capture_output=True).stdout
 (out/name).write_bytes(data);record["members"][name]={"git_path":path,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
f=json.loads((out/"fixture.json").read_text()); assert record["members"]["save.png"]["sha256"]==f["save_sha256"];assert record["members"]["source.png"]["sha256"]==f["source_frame_sha256"]
wad=Path("C:/Users/junny/Documents/Codex/2026-09-19/new-chat/scratch/issue5752_03/data/freedoom2.wad").read_bytes();assert hashlib.sha256(wad).hexdigest()==f["iwad_sha256"]
(out/"freedoom2.wad").write_bytes(wad); record["members"]["freedoom2.wad"]={"sha256":hashlib.sha256(wad).hexdigest(),"bytes":len(wad)}
(root/"fixture-materialization.json").write_text(json.dumps(record,indent=2)+"\n"); print(json.dumps(record))
