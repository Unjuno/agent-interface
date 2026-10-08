import argparse, datetime, json, pathlib, subprocess, sys

IMAGE="python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
WSLC=r"C:\Program Files\WSL\wslc.exe"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("setup","candidate","audit"))
    parser.add_argument("source_dir")
    parser.add_argument("output_dir")
    args=parser.parse_args()
    src=pathlib.Path(args.source_dir).resolve(); out=pathlib.Path(args.output_dir).resolve()
    out.mkdir(parents=True,exist_ok=True)
    stem={"setup":"fixture-setup","candidate":"candidate","audit":"audit"}[args.mode]
    stdout_path=out/(stem+".raw.json" if args.mode!="setup" else "fixture-setup.stdout")
    stderr_path=out/(stem+".stderr")
    meta_path=out/(stem+".exit.json")
    if any(p.exists() for p in (stdout_path,stderr_path,meta_path)):
        raise SystemExit("REFUSE_REPLAY: output path already exists")
    command=[WSLC,"run","--rm","--pull","never","--network","none","--cpus","1","--memory","512M","--volume",str(src)+":/src:ro"]
    if args.mode in ("setup","audit"):
        command += ["--volume",str(out)+(":/out:rw" if args.mode=="setup" else ":/out:ro")]
    command += ["--workdir","/src",IMAGE]
    if args.mode=="setup": command += ["python","-B","setup.py","/out/fixture.json"]
    elif args.mode=="candidate": command += ["python","-B","candidate.py","/src/fixture.json"]
    else: command += ["python","-B","audit.py","/src/fixture.json","/out/candidate.raw.json"]
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        proc=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
        code=proc.returncode; stdout=proc.stdout; stderr=proc.stderr
    except subprocess.TimeoutExpired as e:
        code=124; stdout=e.stdout or b""; stderr=e.stderr or b""
    stdout_path.write_bytes(stdout); stderr_path.write_bytes(stderr)
    meta={"mode":args.mode,"started_utc":started,"finished_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit_code":code,"argv":command,"stdout_bytes":len(stdout),"stderr_bytes":len(stderr),"retry_count":0}
    meta_path.write_text(json.dumps(meta,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps(meta,sort_keys=True,separators=(",",":")))
    return 0 if code==0 else code

if __name__=="__main__": raise SystemExit(main())
