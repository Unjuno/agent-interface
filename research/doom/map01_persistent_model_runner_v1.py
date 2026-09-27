"""Audited initial/resume Luna-low image call for one controller session."""
import hashlib,json,subprocess,sys,time
from pathlib import Path

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    node,cli,prompt_file,working,output,image,instructions,schema,session_id=sys.argv[1:]
    root=Path(output).resolve();root.mkdir(parents=True,exist_ok=False)
    prompt=Path(prompt_file).read_text();(root/"prompt.txt").write_text(prompt)
    common=["--ignore-user-config","--ignore-rules","--json","--model","gpt-5.6-luna",
      "-c",'model_reasoning_effort="low"',"-c","project_doc_max_bytes=0",
      "--output-schema",str(Path(schema).resolve()),"--disable","plugins","--disable","remote_plugin",
      "--disable","shell_snapshot","--disable","shell_tool","--disable","fast_mode",
      "--skip-git-repo-check","-i",str(Path(image).resolve())]
    if session_id=="-":
        args=[node,cli,"exec",*common,"--sandbox","read-only","-c",
              "model_instructions_file="+json.dumps(Path(instructions).resolve().as_posix()),"-"]
        mode="initial"
    else:
        args=[node,cli,"exec","resume",*common,"-c",
              "model_instructions_file="+json.dumps(Path(instructions).resolve().as_posix()),session_id,"-"]
        mode="resume"
    plan={"mode":mode,"session_id_requested":None if session_id=="-" else session_id,
      "args":args,"requested_model":"gpt-5.6-luna","requested_effort":"low",
      "image_sha256":sha(image),"prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),
      "instructions_sha256":sha(instructions),"schema_sha256":sha(schema),"runner_sha256":sha(__file__)}
    (root/"plan.json").write_text(json.dumps(plan,indent=2)+"\n")
    started=time.perf_counter_ns()
    with (root/"stderr.txt").open("wb") as err,(root/"events.jsonl").open("wb") as events:
        p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,cwd=working)
        p.stdin.write(prompt.encode());p.stdin.close()
        for line in p.stdout:events.write(line);events.flush()
        code=p.wait()
    result={"exit_code":code,"started_ns":started,"exited_ns":time.perf_counter_ns(),
      "mode":mode,"requested_model":"gpt-5.6-luna","requested_effort":"low"}
    (root/"process.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result));return code
if __name__=="__main__":raise SystemExit(main())
