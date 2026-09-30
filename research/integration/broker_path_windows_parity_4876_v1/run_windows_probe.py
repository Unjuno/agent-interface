from __future__ import annotations
import argparse, importlib.util, json, os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("frozen_candidate_policy", ROOT / "path_policy.py")
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)

def main(out_path: Path) -> int:
    if out_path.exists():
        print(json.dumps({"decision":"STOP_OUTPUT_EXISTS","path":str(out_path)}))
        return 2
    with tempfile.TemporaryDirectory(prefix="broker-win-path-") as tmp:
        base=Path(tmp)
        repo=base/"repo root"
        outside=base/"outside"
        repo.mkdir(); outside.mkdir()
        sub=repo/"folder space"; sub.mkdir()
        (repo/"plain.txt").write_text("inside",encoding="utf-8")
        (sub/"café 資料.txt").write_text("unicode",encoding="utf-8")
        (repo/"work dir").mkdir()
        (outside/"secret.txt").write_text("outside sentinel",encoding="utf-8")
        try:
            (repo/"inside-link").symlink_to(sub, target_is_directory=True)
            (repo/"outside-link").symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            print(json.dumps({"decision":"STOP_SYMLINK_UNAVAILABLE","error":type(exc).__name__,"detail":str(exc)}))
            return 2
        root=repo.resolve(strict=True)
        cases=[
          ("repo-root","/repo",True,""),
          ("workspace-root","/workspace",True,""),
          ("repo-file","/repo/plain.txt",True,"\\plain.txt"),
          ("workspace-unicode","/workspace/folder space/café 資料.txt",True,"\\folder space\\café 資料.txt"),
          ("repo-dir-space","/repo/work dir",True,"\\work dir"),
          ("in-root-dir-symlink","/repo/inside-link/café 資料.txt",True,"\\folder space\\café 資料.txt"),
          ("host-absolute",str(outside/"secret.txt"),False,None),
          ("drive-absolute","C:\\Windows\\win.ini",False,None),
          ("unc","\\\\server\\share\\secret.txt",False,None),
          ("device-namespace","\\\\?\\C:\\Windows\\win.ini",False,None),
          ("device-dot","\\\\.\\NUL",False,None),
          ("parent-traversal","/repo/../outside/secret.txt",False,None),
          ("encoded-dot","/repo/%2e%2e/outside/secret.txt",False,None),
          ("nested-encoded-dot","/repo/%252e%252e/outside/secret.txt",False,None),
          ("deep-encoded-dot","/repo/%25252e%25252e/outside/secret.txt",False,None),
          ("encoded-separator","/repo/%2f..%2foutside/secret.txt",False,None),
          ("encoded-backslash","/repo/%5c..%5coutside%5csecret.txt",False,None),
          ("raw-backslash","/repo/..\\outside\\secret.txt",False,None),
          ("empty-component","/repo//plain.txt",False,None),
          ("dot-component","/repo/./plain.txt",False,None),
          ("nul","/repo/bad%00name",False,None),
          ("external-symlink","/repo/outside-link/secret.txt",False,None),
          ("missing","/repo/missing.txt",False,None),
          ("win-device-nul","/repo/NUL",False,None),
          ("win-device-con-extension","/repo/CON.txt",False,None),
          ("win-device-aux","/repo/AUX",False,None),
          ("win-device-com1","/repo/COM1.log",False,None),
          ("win-device-lpt9","/repo/LPT9",False,None),
        ]
        results=[]
        for name,value,accepted,suffix in cases:
            try:
                actual=POLICY.resolve_host_path(value,repo)
                error=None
            except (ValueError,OSError) as exc:
                actual=None; error=type(exc).__name__
            expected=None if suffix is None else str(Path(str(root)+suffix))
            results.append({"name":name,"input":value,"expected_accept":accepted,"expected_suffix":suffix,
                            "actual":actual,"error":error,"expected_target":expected})
        data={"schema":"broker-path-windows-parity-4876-v1","allocation":"broker-path-windows-parity-4876-20260927-01",
              "candidate_blob":"cdd0e3d57e08a316fc9df6b55abca8c740db070d","production_broker_blob":"5734f54f318db9ac5e96b2bed6f6bed105ac39ff",
              "python":sys.version,"os":sys.platform,"root":str(root),"case_count":len(results),"cases":results,
              "fixture_symlinks":{"inside":"repo/inside-link -> repo/folder space","outside":"repo/outside-link -> sibling outside/"},
              "decision":"RAW_CAPTURED"}
        out_path.parent.mkdir(parents=True,exist_ok=True)
        out_path.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"captured":len(results),"output":str(out_path),"python":sys.version,"os":sys.platform},sort_keys=True))
        return 0

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--out",type=Path,required=True)
    raise SystemExit(main(p.parse_args().out))

