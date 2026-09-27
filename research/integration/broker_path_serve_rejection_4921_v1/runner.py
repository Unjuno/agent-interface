"""One-shot #4921 serve-boundary integration allocation."""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import broker_under_test as broker

def expected_cases():
    rows=[("valid_repo",None,"valid_repo"),("valid_workspace",None,"valid_workspace")]
    for field in ("schema","image","working"):
        rows.append((field+"_inside_symlink",field,"inside_symlink"))
        for kind in ("traversal","encoded_traversal","absolute","missing","external_symlink","ambiguous_separator"):
            rows.append((field+"_"+kind,field,kind))
    return rows

def main(out_path):
    out_path=Path(out_path)
    with tempfile.TemporaryDirectory(prefix="broker-4921-") as tmp:
        base=Path(tmp); root=base/"repo"; root.mkdir(); outside=base/"outside"; outside.mkdir()
        (root/"schema.json").write_text('{"type":"object"}')
        (root/"image.png").write_bytes(b"fixture")
        (root/"work").mkdir()
        (outside/"schema.json").write_text("outside")
        (outside/"image.png").write_bytes(b"outside")
        (outside/"work").mkdir()
        (root/"inside_file").symlink_to(root/"schema.json")
        (root/"inside_image").symlink_to(root/"image.png")
        (root/"inside_dir").symlink_to(root/"work", target_is_directory=True)
        (root/"escape_file").symlink_to(outside/"schema.json")
        (root/"escape_image").symlink_to(outside/"image.png")
        (root/"escape_dir").symlink_to(outside/"work", target_is_directory=True)
        calls=[]
        def recorder(args, **kwargs):
            calls.append(list(args))
            return SimpleNamespace(returncode=0,stdout='{"mock":"ok"}',stderr="")
        broker.subprocess.run=recorder
        results=[]
        for index,(case_id,field,kind) in enumerate(expected_cases()):
            values={"schema":"/repo/schema.json","image":"/repo/image.png","working":"/repo/work"}
            if kind=="valid_workspace":
                values={"schema":"/workspace/schema.json","image":"/workspace/image.png","working":"/workspace/work"}
            elif kind=="inside_symlink":
                values[field]={"schema":"/repo/inside_file","image":"/repo/inside_image","working":"/repo/inside_dir"}[field]
            elif kind=="traversal": values[field]="/repo/../outside/schema.json"
            elif kind=="encoded_traversal": values[field]="/repo/%252e%252e/outside/schema.json"
            elif kind=="absolute": values[field]=str({"schema":outside/"schema.json","image":outside/"image.png","working":outside/"work"}[field])
            elif kind=="missing": values[field]="/repo/not-present"
            elif kind=="external_symlink":
                values[field]={"schema":"/repo/escape_file","image":"/repo/escape_image","working":"/repo/escape_dir"}[field]
            elif kind=="ambiguous_separator": values[field]="/repo/sub\\..\\outside"
            expected="accept" if kind in ("valid_repo","valid_workspace","inside_symlink") else "reject"
            request_id=f"case-{index:02d}"
            ipc=base/f"ipc-{index:02d}"; ipc.mkdir()
            request={"request_id":request_id,"schema":values["schema"],"image":values["image"],
                     "working":values["working"],"prompt":"inert construction probe"}
            (ipc/f"{request_id}.request.json").write_text(json.dumps(request))
            before=len(calls); exit_code=broker.serve(ipc,root,once=True); added=calls[before:]
            receipt=json.loads((ipc/f"{request_id}.broker.json").read_text())
            response=(ipc/f"{request_id}.response.jsonl").read_text()
            results.append({"case_id":case_id,"field":field,"class":kind,"expected":expected,
                "request_id":request_id,"path_values":values,"exit_code":exit_code,"receipt":receipt,"response":response,
                "subprocess_calls":added,"response_exists":(ipc/f"{request_id}.response.jsonl").is_file(),
                "broker_receipt_count":len(list(ipc.glob("*.broker.json")))})
        raw={"schema":"broker-path-serve-rejection-4921-raw-v1","repo_root":str(root),
             "candidate_source_blob":"frozen-in-FREEZE.json","rows":results,
             "formal_runner_invocations":1,"retries":0}
        out_path.write_text(json.dumps(raw,sort_keys=True,indent=2)+"\n")
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: runner.py RAW.json")
    main(sys.argv[1])
