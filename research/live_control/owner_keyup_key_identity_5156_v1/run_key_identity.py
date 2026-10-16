"""Single bounded host-only key-identity audit experiment."""
import base64, copy, hashlib, json, sys, types

EXPECTED_HASHES = {
    "candidate_auditor": "79f95eadb29bc6cc35036c6ff424cb284e55849ecd76ccd2a841ae186a18d1cf",
    "legacy_auditor": "191fdabdd289e49b03514d1dfc66ba475b885ab078b733a7ef7030daf9cfe906",
    "expected_inventory": "9ef72a837ce4f5d802dcc7fdb72a843a0e768154dbe30897a00f270cfaabde2b",
    "raw_input": "56842934b9f9b13fe0e52d515d31bd0c3d598cdb1cfa8b719dfb4c8ba463cbc2",
}
if len(sys.argv) != 5:
    raise SystemExit("usage: run_key_identity.py CANDIDATE_B64 LEGACY_B64 EXPECTED_B64 RAW_B64")
encoded = dict(zip(EXPECTED_HASHES, sys.argv[1:]))
blobs = {name: base64.b64decode(value, validate=True) for name, value in encoded.items()}
actual_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in blobs.items()}
if actual_hashes != EXPECTED_HASHES:
    raise SystemExit(json.dumps({"status":"STOP_HASH_MISMATCH","expected":EXPECTED_HASHES,"actual":actual_hashes},sort_keys=True))
def module_from(blob, name):
    module = types.ModuleType(name)
    exec(compile(blob.decode("utf-8"), name + ".py", "exec"), module.__dict__)
    return module
candidate = module_from(blobs["candidate_auditor"], "candidate")
legacy = module_from(blobs["legacy_auditor"], "legacy")
expected = json.loads(blobs["expected_inventory"])
original = json.loads(blobs["raw_input"])["records"]
def result_for(module, records):
    return sorted(module.audit(expected, records))
mut_explicit = copy.deepcopy(original)
mut_explicit[0]["key"] = "tampered-key"
mut_cleanup = copy.deepcopy(original)
mut_cleanup[2]["key"] = "a"
missing_key = copy.deepcopy(original)
del missing_key[0]["key"]
missing_row = copy.deepcopy(original)
missing_row.pop(0)
checks = {
    "candidate_pristine": result_for(candidate, original),
    "candidate_explicit_key_tamper": result_for(candidate, mut_explicit),
    "candidate_cleanup_key_tamper": result_for(candidate, mut_cleanup),
    "candidate_missing_key": result_for(candidate, missing_key),
    "candidate_missing_row": result_for(candidate, missing_row),
    "legacy_explicit_key_tamper": result_for(legacy, mut_explicit),
    "legacy_cleanup_key_tamper": result_for(legacy, mut_cleanup),
}
result = {
    "status":"PASS_KEY_IDENTITY_AUDIT_HOST_ONLY",
    "scope":"synthetic immutable PR #5467 inputs; host-only construction/integrity",
    "source_hashes":actual_hashes,
    "checks":checks,
    "legacy_fail_open_reproduced":checks["legacy_explicit_key_tamper"] == [] and checks["legacy_cleanup_key_tamper"] == [],
    "candidate_rejects_explicit_key":any(x == "release_identity_mismatch:explicit-a-01" for x in checks["candidate_explicit_key_tamper"]),
    "candidate_rejects_cleanup_key":any(x == "release_identity_mismatch:cleanup-b-01" for x in checks["candidate_cleanup_key_tamper"]),
    "candidate_rejects_missing_key":any(":missing:key" in x for x in checks["candidate_missing_key"]),
    "candidate_rejects_missing_row":any(x == "expected_release_missing:explicit-a-01" for x in checks["candidate_missing_row"]),
}
print(json.dumps(result, sort_keys=True))
