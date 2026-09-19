"""Controlled Luna-low visual grounding adapter with complete usage records."""
import hashlib,json,subprocess,time
from pathlib import Path

try:
    from .compiled_form_grounding_v1 import validate
except ImportError:
    from compiled_form_grounding_v1 import validate

HERE=Path(__file__).resolve().parent
WINDOWS_PYTHON=Path("/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe")
NODE=r"C:\Program Files\nodejs\node.exe"
CLI=r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
RUNNER=HERE/"target_handle_model_runner_v2.py"
SCHEMA=HERE/"compiled_form_grounding_schema_v1.json"
INSTRUCTIONS=HERE/"compiled_form_grounding_responder_v1.txt"
USAGE_FIELDS=("input_tokens","cached_input_tokens","cache_write_input_tokens",
              "output_tokens","reasoning_output_tokens")

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def windows_path(path):
    return subprocess.run(["wslpath","-w",str(Path(path).resolve())],capture_output=True,
                          text=True,check=True).stdout.strip()

def parse_output(output):
    output=Path(output)
    events=[json.loads(line) for line in (output/"events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages=[row["item"]["text"] for row in events if row.get("type")=="item.completed"
              and row.get("item",{}).get("type")=="agent_message"]
    turns=[row for row in events if row.get("type")=="turn.completed"]
    threads=[row["thread_id"] for row in events if row.get("type")=="thread.started"]
    if len({len(messages),len(turns),len(threads)})!=1:
        raise ValueError("one message, completed turn and thread required")
    if len(messages)!=1:
        raise ValueError("exactly one completed model result required")
    raw=json.loads(messages[0]);grounding=validate(raw);usage=turns[0].get("usage")
    if type(usage) is not dict or any(type(usage.get(field)) is not int or usage[field]<0
                                      for field in USAGE_FIELDS):
        raise ValueError("complete nonnegative model usage required")
    process=json.loads((output/"process.json").read_text(encoding="utf-8"))
    if process.get("exit_code")!=0 or process.get("requested_model")!="gpt-5.6-luna" or process.get("requested_effort")!="low":
        raise ValueError("successful Luna-low process required")
    return {"raw":raw,"grounding":grounding,"usage":usage,"call_id":threads[0],
            "runner_ms":(process["exited_ns"]-process["started_ns"])/1e6,
            "requested_model":process["requested_model"],
            "requested_effort":process["requested_effort"],"cost":None}

def call(output,prompt,image,workspace):
    output=Path(output);prompt_path=output.parent/(output.name+"-prompt.txt")
    prompt_path.write_text(prompt,encoding="utf-8",newline="\n")
    command=[str(WINDOWS_PYTHON),windows_path(RUNNER),NODE,CLI,windows_path(prompt_path),
        windows_path(workspace),windows_path(output),"coordinate",windows_path(image),
        windows_path(INSTRUCTIONS),windows_path(SCHEMA)]
    started=time.perf_counter_ns();completed=subprocess.run(command,capture_output=True,timeout=90)
    ended=time.perf_counter_ns()
    (output.parent/(output.name+"-stdout.txt")).write_bytes(completed.stdout)
    (output.parent/(output.name+"-stderr.txt")).write_bytes(completed.stderr)
    if completed.returncode!=0:raise RuntimeError("grounding model call failed; no retry")
    result=parse_output(output);result["caller_elapsed_ms"]=(ended-started)/1e6
    result["image_sha256"]=sha(image);result["prompt_sha256"]=hashlib.sha256(prompt.encode()).hexdigest()
    return result
