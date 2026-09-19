import hashlib
import json

STATES = {
    "doctor", "model_attempt", "observation", "dispatch", "refusal",
    "effect", "repair", "release", "cleanup",
}
STATUSES = {"success", "partial", "refused", "stale_invalidated", "cleanup_failed"}
FIELDS = {
    "schema", "program_completed", "task_success", "authority_granted",
    "status", "partial_effects", "cleanup_error", "lifecycle", "usage",
}

FIXTURES = [
    {"schema":"golden-v3-result-v1","program_completed":True,"task_success":True,"authority_granted":False,"status":"success","partial_effects":[],"cleanup_error":None,"lifecycle":["doctor","model_attempt","observation","dispatch","effect","release"],"usage":{"input":1}},
    {"schema":"golden-v3-result-v1","program_completed":False,"task_success":False,"authority_granted":False,"status":"partial","partial_effects":["effect-1"],"cleanup_error":None,"lifecycle":["dispatch","effect","release"],"usage":{}},
    {"schema":"golden-v3-result-v1","program_completed":False,"task_success":False,"authority_granted":False,"status":"refused","partial_effects":[],"cleanup_error":None,"lifecycle":["observation","refusal"],"usage":{}},
    {"schema":"golden-v3-result-v1","program_completed":False,"task_success":False,"authority_granted":False,"status":"stale_invalidated","partial_effects":[],"cleanup_error":None,"lifecycle":["observation","repair","refusal"],"usage":{}},
    {"schema":"golden-v3-result-v1","program_completed":False,"task_success":False,"authority_granted":False,"status":"cleanup_failed","partial_effects":["effect-1"],"cleanup_error":"CLOSE_FAILED","lifecycle":["dispatch","effect","cleanup"],"usage":{}},
]

def validate(row):
    assert set(row) == FIELDS
    assert row["schema"] == "golden-v3-result-v1"
    assert type(row["program_completed"]) is bool
    assert type(row["task_success"]) is bool
    assert row["authority_granted"] is False
    assert row["status"] in STATUSES
    assert type(row["partial_effects"]) is list
    assert row["cleanup_error"] is None or type(row["cleanup_error"]) is str
    assert type(row["lifecycle"]) is list and set(row["lifecycle"]) <= STATES
    assert type(row["usage"]) is dict
    if row["status"] == "success":
        assert row["program_completed"] and row["task_success"]
        assert row["cleanup_error"] is None
    if row["cleanup_error"] is not None:
        assert row["status"] == "cleanup_failed"
        assert row["task_success"] is False
    if row["status"] == "partial":
        assert row["partial_effects"]
        assert not (row["program_completed"] and row["task_success"])

def rejected(row):
    try:
        validate(row)
    except AssertionError:
        return True
    return False

def main():
    for row in FIXTURES:
        validate(row)
    bad = [
        {**FIXTURES[0], "authority_granted": True},
        {**FIXTURES[0], "status": "unknown"},
        {**FIXTURES[0], "lifecycle": ["unknown"]},
        {**FIXTURES[0], "cleanup_error": "CLOSE_FAILED"},
        {**FIXTURES[1], "partial_effects": []},
        {**FIXTURES[0], "program_completed": False},
    ]
    assert all(rejected(row) for row in bad)
    digest = hashlib.sha256(json.dumps({"accepted": FIXTURES, "rejected": bad}, sort_keys=True).encode()).hexdigest()
    print(json.dumps({"accepted":len(FIXTURES),"rejected":len(bad),"states":len(STATES),"authority_grants":0,"validator":"PASS","digest":digest,"model":0,"gui":0,"network":0,"input":0}, sort_keys=True))

if __name__ == "__main__":
    main()
