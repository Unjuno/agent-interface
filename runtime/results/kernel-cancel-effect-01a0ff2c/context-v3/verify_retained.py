from pathlib import Path
import hashlib, json, re

root = Path(__file__).resolve().parent
manifest = json.loads((root / "PUBLIC_MANIFEST.json").read_text(encoding="utf-8"))
for row in manifest["files"]:
    data = (root / row["path"]).read_bytes()
    if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise ValueError("manifest mismatch: " + row["path"])
context = json.loads((root / "SOURCE_REFRESH.json").read_text(encoding="utf-8"))
for arm, rows in context["pins"].items():
    for row in rows:
        data = (root / (arm + "-source") / row["path"]).read_bytes()
        oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"] or oid != row["git_blob"]:
            raise ValueError("source pin mismatch")
receipts = json.loads((root / "RUN_RECEIPTS.json").read_text(encoding="utf-8"))
transforms = {r["path"]: r for r in json.loads((root / "PUBLICATION_TRANSFORMS.json").read_text(encoding="utf-8"))["transforms"]}
expected = {"before-normal": (1, {"test_stop_after_begin_without_receipt_preserves_possible_effect", "test_stale_cancel_refusal_then_fresh_release_preserves_possible_effect"}), "after-normal": (0, set()), "after-optimized": (0, set())}
if {r["id"] for r in receipts} != set(expected) or len(receipts) != 3:
    raise ValueError("receipt coverage")
for row in receipts:
    code, failures = expected[row["id"]]
    if row["exit_code"] != code or row["methods"] != 40 or row["timed_out"] or row["error_methods"] or set(row["failed_methods"]) != failures:
        raise ValueError("unexpected actual receipt")
    for suffix in ["stdout", "stderr"]:
        name = row["id"] + "." + suffix + ".log"
        data = (root / name).read_bytes()
        if name in transforms:
            t = transforms[name]
            if t["original_sha256"] != row[suffix + "_sha256"] or t["original_bytes"] != row[suffix + "_bytes"] or t["public_sha256"] != hashlib.sha256(data).hexdigest():
                raise ValueError("log projection binding")
        elif len(data) != row[suffix + "_bytes"] or hashlib.sha256(data).hexdigest() != row[suffix + "_sha256"]:
            raise ValueError("original log binding")
    log = (root / (row["id"] + ".stderr.log")).read_text(encoding="utf-8")
    if re.findall(r"^Ran (\d+) tests? in ", log, re.M) != ["40"] or set(re.findall(r"^FAIL: (\w+) \(", log, re.M)) != failures or re.findall(r"^ERROR:", log, re.M):
        raise ValueError("actual log outcome")
print(json.dumps({"files": len(manifest["files"]), "source_pins": 16, "actual_receipts": 3, "producer_invocations": 0, "retained_audit": "PASS"}))
