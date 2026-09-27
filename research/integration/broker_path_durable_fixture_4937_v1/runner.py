"""One-shot durable-fixture #4937 actual serve() candidate allocation."""
from __future__ import annotations
import hashlib,json,os,stat,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import broker_under_test as broker

def schedule():
    out=[("valid_repo",None,"valid_repo"),("valid_workspace",None,"valid_workspace")]
    for field in ("schema","image","working"):
        out.append((field+"_inside_symlink",field,"inside_symlink"))
        for kind in ("traversal","encoded_traversal","absolute","missing","external_symlink","ambiguous_separator"):
            out.append((field+"_"+kind,field,kind))
    return out

def inventory(base):
    rows=[]
    for cur,dirs,files in os.walk(base,followlinks=False):
        names=sorted(dirs+files)
        for name in names:
            p=Path(cur)/name; st=p.lstat(); rel=p.relative_to(base).as_posix()
            if stat.S_ISLNK(st.st_mode): kind="symlink"; target=os.readlink(p); digest=None
            elif stat.S_ISDIR(st.st_mode): kind="directory"; target=None; digest=None
            elif stat.S_ISREG(st.st_mode): kind="file"; target=None; digest=hashlib.sha256(p.read_bytes()).hexdigest()
            else: kind="other"; target=None; digest=None
            rows.append({"path":rel,"kind":kind,"size":st.st_size,"link_target":target,"sha256":digest})
    return sorted(rows,key=lambda x:x["path"])

def main(raw_path,manifest_path):
    raw_path=Path(raw_path); base=raw_path.parent/"fixtures"; base.mkdir(parents=True,exist_ok=False)
    root=base/"repo"; outside=base/"outside"; root.mkdir(); outside.mkdir()
    (root/"schema.json").write_text('{"type":"object"}')
    (root/"image.png").write_bytes(b"fixture-image")
    (root/"work").mkdir()
    (outside/"schema.json").write_text("outside-schema")
    (outside/"image.png").write_bytes(b"outside-image")
    (outside/"work").mkdir()
    (root/"inside_file").symlink_to(root/"schema.json")
    (root/"inside_image").symlink_to(root/"image.png")
    (root/"inside_dir").symlink_to(root/"work",target_is_directory=True)
    (root/"escape_file").symlink_to(outside/"schema.json")
    (root/"escape_image").symlink_to(outside/"image.png")
    (root/"escape_dir").symlink_to(outside/"work",target_is_directory=True)
    initial=inventory(base)
    calls=[]
    def recorder(args,**kwargs):
        calls.append(list(args)); return SimpleNamespace(returncode=0,stdout='{"mock":"ok"}',stderr="")
    broker.subprocess.run=recorder
    rows=[]
    for i,(case_id,field,kind) in enumerate(schedule()):
        values={"schema":"/repo/schema.json","image":"/repo/image.png","working":"/repo/work"}
        if kind=="valid_workspace": values={"schema":"/workspace/schema.json","image":"/workspace/image.png","working":"/workspace/work"}
        elif kind=="inside_symlink": values[field]={"schema":"/repo/inside_file","image":"/repo/inside_image","working":"/repo/inside_dir"}[field]
        elif kind=="traversal": values[field]="/repo/../outside/schema.json"
        elif kind=="encoded_traversal": values[field]="/repo/%252e%252e/outside/schema.json"
        elif kind=="absolute": values[field]=str({"schema":outside/"schema.json","image":outside/"image.png","working":outside/"work"}[field])
        elif kind=="missing": values[field]="/repo/not-present"
        elif kind=="external_symlink": values[field]={"schema":"/repo/escape_file","image":"/repo/escape_image","working":"/repo/escape_dir"}[field]
        elif kind=="ambiguous_separator": values[field]="/repo/sub\\..\\outside"
        expected="accept" if kind in ("valid_repo","valid_workspace","inside_symlink") else "reject"
        rid=f"case-{i:02d}"; ipc=base/f"ipc-{i:02d}"; ipc.mkdir()
        request={"request_id":rid,"schema":values["schema"],"image":values["image"],"working":values["working"],"prompt":"inert construction probe"}
        (ipc/f"{rid}.request.json").write_text(json.dumps(request))
        before=len(calls); exit_code=broker.serve(ipc,root,once=True); added=calls[before:]
        receipt=json.loads((ipc/f"{rid}.broker.json").read_text())
        response=(ipc/f"{rid}.response.jsonl").read_text()
        rows.append({"case_id":case_id,"request_id":rid,"field":field,"class":kind,"expected":expected,
          "path_values":values,"exit_code":exit_code,"receipt":receipt,"response":response,
          "subprocess_calls":added,"response_exists":(ipc/f"{rid}.response.jsonl").is_file(),
          "broker_receipt_count":len(list(ipc.glob("*.broker.json")))})
    final=inventory(base)
    manifest={"schema":"broker-path-4937-fixture-manifest-v1","base":str(base),"repo_root":str(root),
      "outside_root":str(outside),"entries":final,"initial_equals_final":initial==final}
    manifest_bytes=(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode()
    Path(manifest_path).write_bytes(manifest_bytes)
    raw={"schema":"broker-path-durable-fixture-4937-raw-v1","allocation":"broker-path-durable-fixture-4937-20260928-01",
      "fixture_base":str(base),"repo_root":str(root),"outside_root":str(outside),
      "fixture_manifest_path":str(Path(manifest_path)),"fixture_manifest_sha256":hashlib.sha256(manifest_bytes).hexdigest(),
      "fixture_unchanged_during_run":initial==final,"rows":rows,"formal_runner_invocations":1,"retries":0}
    raw_path.write_text(json.dumps(raw,sort_keys=True,indent=2)+"\n")
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: runner.py RAW.json FIXTURE_MANIFEST.json")
    main(sys.argv[1],sys.argv[2])
