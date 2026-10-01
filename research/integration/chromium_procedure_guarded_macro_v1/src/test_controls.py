from compiler import CompileError, compile_guarded, validate_guarded_artifact, evaluate_guarded, EXPECTED_METHOD

def ex():
    return {"token":"secret-task1","context":{"focus":1,"surface":1,"geometry":[0,0,100,100]},"grounding":{"field_point":[1,2],"submit_point":[3,4],"method":dict(EXPECTED_METHOD)}}

def state(field="eligible", submit="eligible"):
    return {"token":"fresh","controller":{"field_handle":"f","field_status":field,"submit_handle":"s","submit_status":submit},"evaluator":{"current_field_handle":"f","current_submit_handle":"s"},"context":{"focus":1,"surface":1,"geometry":[0,0,100,100]}}

def must_reject(fn):
    try: fn()
    except CompileError: return
    raise AssertionError("expected CompileError")

a=compile_guarded(ex())
assert "secret-task1" not in repr(a)
assert evaluate_guarded(a,state("missing"))["decision"] == "YIELD"
assert evaluate_guarded(a,state("stale"))["decision"] == "YIELD"
assert evaluate_guarded(a,state("eligible","missing"))["decision"] == "YIELD"
bad=ex(); bad["grounding"]["method"]["first_action"]="unknown"
must_reject(lambda: compile_guarded(bad))
bad_art=dict(a); bad_art["field_point"]=[1,2]
must_reject(lambda: validate_guarded_artifact(bad_art))
bad_art=dict(a); bad_art["authority"]="task"
must_reject(lambda: validate_guarded_artifact(bad_art))
print("PASS controls=6")
