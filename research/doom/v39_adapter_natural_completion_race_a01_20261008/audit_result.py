import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parent; f=json.loads((R/"FREEZE.json").read_text()); b=(R/"RESULT.json").read_bytes(); d=json.loads(b)
blob=lambda x:hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
sources=[R/"source"/n for n in ("controller_v39.py","persistent_planner_adapter_v2.py","codex_app_server_client_v2.py")]
assert [blob(p.read_bytes()) for p in sources]==[x["git_blob"] for x in f["sources"]]
assert hashlib.sha256(b).hexdigest()==(R/"RESULT_SHA256.txt").read_text().split()[0].lower()
assert d["main"]==f["main_commit"] and d["status"]=="PASS_COMPLETION_RETAINED_BUT_ANSWER_INVALIDATED"
e=[x["event"] for x in d["events"]]; assert e.index("executor_cancel_flush")<e.index("interrupt_request_written")<e.index("turn_completed_notification_received")<e.index("interrupt_response_received")
assert d["turn_result"]=={"status":"completed","cancellation_requested":True,"answer_eligible":False,"answer":None,"error":"answer belongs to an invalidated observation"}
rep=json.loads((R/"reproduction.stdout").read_text(encoding="utf-8-sig")); assert rep["main"]==f["main_commit"] and rep["turn_result"]==d["turn_result"]; assert [x["event"] for x in rep["events"]]==e
print("PASS_INDEPENDENT_SOURCE_AND_RESULT_AUDIT",f["main_commit"],len(sources),hashlib.sha256(b).hexdigest())
