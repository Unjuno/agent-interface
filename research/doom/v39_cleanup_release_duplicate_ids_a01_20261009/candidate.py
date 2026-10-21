import base64,hashlib,json,subprocess
REPOSITORY="Unjuno/agent-interface"
REF="0455b0079ca29bcfe85153f280e592f5e96528f6"
PATH="research/doom/doom_controller_failure_cleanup_v1.py"
GIT_BLOB="50c63fa83969ed518a91e39c08d1ee52064eb636"
SHA256="bc8d3550e6c2d057c7b615b38e424de3497418547e835490429f526853e1fe28"
obj=json.loads(subprocess.check_output(["gh","api",f"repos/{REPOSITORY}/contents/{PATH}?ref={REF}"]))
src=base64.b64decode("".join(obj["content"].split()))
if obj["sha"]!=GIT_BLOB or hashlib.sha256(src).hexdigest()!=SHA256: raise RuntimeError("source identity mismatch")
ns={"__name__":"pinned_cleanup_module"};exec(compile(src,PATH,"exec"),ns)
Cleanup=ns["ControllerFailureCleanup"]
class Planner:
 def close(self,timeout=1): return None
class Reader:
 def join(self,timeout=None): return None
 def is_alive(self): return False
class File:
 def __init__(self,s): self.s=s
 def write_text(self,t): self.s.text=t;return len(t)
class Sink:
 def __init__(self): self.text=None
 def __truediv__(self,n):
  if n!="controller-failure.json": raise AssertionError("path")
  return File(self)
def accepted(token): return {"event":"accepted","id":"cmd-1","intent_token":token}
def terminal(token):
 r={"verified":True,"keys_down":[],"buttons_down":[]}
 if token is not None:r["intent_token"]=token
 return {"event":"terminal","id":"cmd-1","release":r}
def run(name,events):
 sink=Sink();scope=Cleanup(Planner(),sink);scope.observe_output(events,Reader(),lambda p,t:None,None,[])
 try:
  with scope:
   scope.set_stage("source_refresh");raise RuntimeError("synthetic primary failure")
 except RuntimeError as e:
  if str(e)!="synthetic primary failure":raise
 if sink.text is None:raise RuntimeError("receipt not captured")
 r=json.loads(sink.text)
 return {"case_id":name,"event_rows":len(events),"input_terminals_complete":r["input_terminals_complete"],"input_releases_verified_empty":r["input_releases_verified_empty"],"input_release_verified_empty":r["input_release_verified_empty"]}
cases=[
 ("single_matching_token",[accepted("lease-A"),terminal("lease-A")]),
 ("single_legacy_tokenless_terminal",[accepted("lease-A"),terminal(None)]),
 ("single_mismatched_token",[accepted("lease-A"),terminal("lease-B")]),
 ("missing_terminal",[accepted("lease-A")]),
 ("duplicate_accept_unreleased_first",[accepted("lease-A"),accepted("lease-B"),terminal("lease-B")]),
 ("duplicate_terminals_matching_last",[accepted("lease-A"),terminal("lease-B"),terminal("lease-A")]),
 ("duplicate_terminals_mismatching_last",[accepted("lease-A"),terminal("lease-A"),terminal("lease-B")]),
]
print(json.dumps({"schema":"issue59-cleanup-duplicate-id-candidate-v1","pinned_source_ref":REF,"pinned_source_path":PATH,"pinned_source_git_blob":GIT_BLOB,"pinned_source_sha256":SHA256,"candidate_invocations":1,"runtime_invocations":0,"live_allocations":0,"rows":[run(n,e) for n,e in cases]},sort_keys=True,separators=(",",":")))
