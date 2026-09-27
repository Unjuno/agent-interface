"""Host-IPC runner preserving raw events and counting assistant messages by type."""
from __future__ import annotations
import hashlib,json,os,sys,tempfile,time,uuid
from pathlib import Path

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic_json(path,value):
    fd,name=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as stream:
            json.dump(value,stream,indent=2);stream.write("\n");stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally: Path(name).unlink(missing_ok=True)
def main():
    _node,_legacy,prompt_file,working,output,mode,image,instructions,schema=sys.argv[1:]
    if mode not in ("coordinate","handle"): raise ValueError("unsupported mode")
    root=Path(output).resolve();root.mkdir(parents=True,exist_ok=False)
    prompt=Path(prompt_file).read_text(encoding="utf-8")
    ipc=Path(os.environ.get("HOST_MODEL_IPC_DIR","")).resolve()
    if not ipc.is_dir(): raise RuntimeError("HOST_MODEL_IPC_DIR missing")
    image_path=None if image=="-" else Path(image).resolve();request_id=uuid.uuid4().hex
    request={"request_id":request_id,"mode":mode,"prompt":prompt,"working":str(Path(working).resolve()),
      "image":None if image_path is None else str(image_path),"image_sha256":None if image_path is None else sha(image_path),
      "instructions":str(Path(instructions).resolve()),"instructions_sha256":sha(Path(instructions)),
      "schema":str(Path(schema).resolve()),"schema_sha256":sha(Path(schema)),"runner":"container_host_model_ipc_runner_v27",
      "authority_granted":False}
    (root/"prompt.txt").write_text(prompt,encoding="utf-8",newline="\n")
    (root/"plan.json").write_text(json.dumps(request,indent=2)+"\n",encoding="utf-8",newline="\n")
    request_path=ipc/f"{request_id}.request.json";response_path=ipc/f"{request_id}.response.jsonl"
    started=time.perf_counter_ns();atomic_json(request_path,request)
    deadline=time.monotonic()+float(os.environ.get("HOST_MODEL_IPC_TIMEOUT_S","30"))
    while not response_path.exists():
        if time.monotonic()>=deadline: raise TimeoutError("host IPC response timeout; no retry")
        time.sleep(.025)
    shutil_data=response_path.read_bytes();(root/"events.jsonl").write_bytes(shutil_data)
    events=[json.loads(line) for line in shutil_data.decode("utf-8").splitlines() if line.strip()]
    turns=[row for row in events if row.get("type")=="turn.completed"]
    messages=[row for row in events if row.get("type")=="item.completed" and isinstance(row.get("item"),dict)
              and row["item"].get("type")=="agent_message"]
    if len(turns)!=1 or len(messages)!=1: raise RuntimeError("exactly one completed turn and assistant message required")
    receipt={"exit_code":0,"requested_model":"gpt-5.6-luna","requested_effort":"low","mode":mode,
      "boundary":"container-to-host-model-ipc-replay","authority_granted":False,"request_id":request_id,
      "started_ns":started,"exited_ns":time.perf_counter_ns(),"event_count":len(events),
      "assistant_message_count":len(messages),"completed_turn_count":len(turns),
      "ignored_non_assistant_item_completed_count":sum(row.get("type")=="item.completed" and
        (not isinstance(row.get("item"),dict) or row["item"].get("type")!="agent_message") for row in events),
      "raw_response_sha256":hashlib.sha256(shutil_data).hexdigest()}
    (root/"process.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    return 0
if __name__=="__main__": raise SystemExit(main())
