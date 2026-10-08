import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parent
f=json.loads((R/"FREEZE_A02.json").read_text())
b=(R/"RESULT_A02.json").read_bytes()
g=lambda x:hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
src=[R/"source"/n for n in ("controller_v39.py","persistent_planner_adapter_v2.py","codex_app_server_client_v2.py")]
assert [g(x.read_bytes()) for x in src]==[x["git_blob"] for x in f["sources"]]
assert hashlib.sha256(b).hexdigest()==(R/"RESULT_A02.sha256").read_text().split()[0]
d=json.loads(b)
assert d["main"]==f["main_commit"]
assert d["status"]=="PASS_EXACT_READER_ROUTES_COMPLETION_BEFORE_INTERRUPT_REPLY"
e=[x["event"] for x in d["events"]]
assert e.index("executor_cancel_flush")<e.index("interrupt_request_written")<e.index("client_received_turn/completed")<e.index("turn_completion_consumed")<e.index("interrupt_response_injected")<e.index("client_received_1")<e.index("verified_empty_terminal_observed")
assert d["completion_consumed_before_interrupt_response"] is True
assert d["turn_result"]=={"status":"completed","cancellation_requested":True,"answer_eligible":False,"answer":None,"error":"answer belongs to an invalidated observation"}
assert d["helper_terminal"]["release"]=={"verified":True,"keys_down":[],"buttons_down":[]}
rep=json.loads((R/"candidate_A02.stdout").read_text(encoding="utf-8-sig"))
assert rep["status"]==d["status"] and [x["event"] for x in rep["events"]]==e
print("PASS_A02_READER_SOURCE_RESULT_AUDIT",f["main_commit"],len(src),hashlib.sha256(b).hexdigest())
