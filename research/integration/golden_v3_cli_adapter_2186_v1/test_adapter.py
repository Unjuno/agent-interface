from adapter import adapt_dispatch

def test_success():
 r=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":True,"partial_effects":[]}})
 assert r["status"]=="success" and r["task_success"] is True and r["authority_granted"] is False

def test_partial():
 r=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":False,"partial_effects":["A1"]}})
 assert r["status"]=="partial" and r["task_success"] is False

def test_refusal():
 r=adapt_dispatch({"status":"backend_unavailable","error":"x"})
 assert r["status"]=="refused" and r["program_completed"] is False

def test_cleanup_failure():
 r=adapt_dispatch({"status":"returned","result":{"program_completed":True,"task_success":True},"cleanup_error":"close"})
 assert r["status"]=="partial" and r["task_success"] is False
