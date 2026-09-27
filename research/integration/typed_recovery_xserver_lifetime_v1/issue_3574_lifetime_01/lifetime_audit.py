#!/usr/bin/env python3
"""Raw-only independent audit; imports no X11, runner, or candidate validator."""
import base64
import hashlib
import json
from pathlib import Path
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def typed_equal(a, b):
    return a == b and set(a) == {"backend", "top_level_client_id", "transient_for"}


def exact(receipt, current):
    if (receipt.get("authority") != "none" or receipt.get("task_input_granted") is not False
            or receipt.get("action_admission_eligible") is not False):
        return "INVALID"
    a, b = receipt.get("identity"), current
    if not isinstance(a, dict) or not isinstance(b, dict):
        return "INVALID"
    for k, typ, mandatory in (("backend", str, True),
                              ("top_level_client_id", int, True),
                              ("transient_for", int, False)):
        for v in (a, b):
            e = v.get(k)
            if not isinstance(e, dict) or e.get("state") not in ("KNOWN", "KNOWN_NULL", "UNKNOWN"):
                return "INVALID"
            if mandatory and e.get("state") != "KNOWN":
                return "INVALID"
            if e.get("state") == "KNOWN" and ("value" not in e or type(e["value"]) is not typ):
                return "INVALID"
            if e.get("state") != "KNOWN" and "value" in e:
                return "INVALID"
    for k in ("backend", "top_level_client_id"):
        if a[k] != b[k]:
            return "MISMATCH"
    if "UNKNOWN" in (a["transient_for"]["state"], b["transient_for"]["state"]):
        return "CORE_MATCH_REFINEMENT_UNKNOWN"
    va = None if a["transient_for"]["state"] == "KNOWN_NULL" else a["transient_for"]["value"]
    vb = None if b["transient_for"]["state"] == "KNOWN_NULL" else b["transient_for"]["value"]
    return "EXACT_MATCH" if va == vb else "MISMATCH"


def audit(root):
    freeze_bytes = Path("/freeze/freeze.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    raw_bytes = (root / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    if raw.get("allocation_id") != "issue3574-lifetime-01" or raw.get("disposition") != "HOLD_PENDING_INDEPENDENT_AUDIT":
        raise ValueError("allocation/disposition mismatch")
    if raw.get("network") != "none" or raw.get("input_calls") != 0 or raw.get("failure") is not None:
        raise ValueError("authority/network/failure boundary mismatch")
    if raw.get("freeze_manifest_sha256") != sha(freeze_bytes):
        raise ValueError("freeze manifest hash mismatch")
    if raw.get("source_commit") != freeze.get("source_commit") or raw.get("container_image_id") != freeze.get("container_image_id"):
        raise ValueError("source/image identity mismatch")
    for name, expected in freeze["sha256"].items():
        if sha((Path("/freeze") / name).read_bytes()) != expected:
            raise ValueError("frozen source SHA mismatch: " + name)
    validator_data = (Path("/freeze") / "validator_881_frozen.py").read_bytes()
    git_hash = hashlib.sha1(b"blob " + str(len(validator_data)).encode() + b"\0" + validator_data).hexdigest()
    if git_hash != freeze.get("validator_git_blob_sha1"):
        raise ValueError("exact #881 validator Git blob mismatch")
    if len(raw.get("pairs", [])) != 4 or len(raw.get("classification_rows", [])) != 16:
        raise ValueError("formal denominator mismatch")
    expected = {}
    pixel_hashes = []
    instance_ids, server_pids, fixture_pids, xids = set(), set(), set(), set()
    for pair in raw["pairs"]:
        rep, old, new = pair["rep"], pair["G1"], pair["G2"]
        if old["rep"] != rep or new["rep"] != rep or old["generation"] != "G1" or new["generation"] != "G2":
            raise ValueError("generation labels mismatch")
        for gen in (old, new):
            f, srv = gen["fixture"], gen["server"]
            if (f.get("geometry") != [80, 80, 240, 160] or f.get("title") != "lifetime-902"
                    or f.get("wm_class") != ["lifetime-902", "Lifetime902"]
                    or f.get("transient_present") is not False or f.get("pixel_bytes") != 153600):
                raise ValueError("fixture semantics mismatch")
            pixels = base64.b64decode(f["pixel_b64"], validate=True)
            if len(pixels) != 153600 or sha(pixels) != f.get("pixel_sha256"):
                raise ValueError("pixel byte/hash mismatch")
            pixel_hashes.append(sha(pixels))
            if f.get("root_xid") != old["fixture"].get("root_xid"):
                raise ValueError("root XID changed")
            if f.get("xres", {}).get("version") != [1, 2]:
                raise ValueError("XRes version mismatch")
            pids = f.get("xres_local_pids", [])
            if pids != [f.get("pid")]:
                raise ValueError("XRes owner PID mismatch")
            xres_pids = [pid for item in f["xres"]["rows"]
                         if item["mask"] & 2 for pid in item["values"]]
            if xres_pids != [f.get("pid")]:
                raise ValueError("raw XRes LocalClientPID does not identify fixture process")
            if not f.get("pid_start_ticks") or not srv.get("pid_start_ticks"):
                raise ValueError("missing process incarnation")
            cleanup = gen.get("cleanup", {})
            if cleanup.get("fixture_reaped") is not True or cleanup.get("xvfb_reaped") is not True or cleanup.get("socket_disappeared") is not True:
                raise ValueError("lifecycle cleanup witness missing")
            if gen.get("authority") != "none" or gen.get("task_input_granted") is not False or gen.get("input_calls") != 0:
                raise ValueError("generation has authority/input")
            instance_ids.add(gen["server_instance_id"])
            server_pids.add(srv["pid"])
            fixture_pids.add(f["pid"])
            xids.add(f["xid"])
        if old["server_instance_id"] == new["server_instance_id"]:
            raise ValueError("server-instance token collision")
        if old["server"]["pid"] == new["server"]["pid"] or old["server"]["pid_start_ticks"] == new["server"]["pid_start_ticks"]:
            raise ValueError("Xvfb process incarnation did not change")
        if old["fixture"]["pid"] == new["fixture"]["pid"] or old["fixture"]["pid_start_ticks"] == new["fixture"]["pid_start_ticks"]:
            raise ValueError("fixture process incarnation did not change")
        if old["fixture"]["xid"] != new["fixture"]["xid"]:
            raise ValueError("XID not reused")
        p1, p2 = base64.b64decode(old["fixture"]["pixel_b64"]), base64.b64decode(new["fixture"]["pixel_b64"])
        if p1 != p2:
            raise ValueError("pixel bytes differ across X-server generations")
        a = pair["typed_identity_G1"]
        b = pair["typed_identity_G2"]
        if not typed_equal(a, b):
            raise ValueError("typed identity differs; no stale exact-match discriminator")
        if a["top_level_client_id"] != {"state": "KNOWN", "value": old["fixture"]["xid"]}:
            raise ValueError("typed client ID not bound to observed XID")
        if a["transient_for"] != {"state": "KNOWN_NULL"}:
            raise ValueError("transient absence not represented as KNOWN_NULL")
        for key, source, current, expected_value in (
            ("current_fresh", a, a, "EXACT_MATCH"),
            ("current_stale", a, b, "EXACT_MATCH"),
            ("lifetime_fresh", a, a, "EXACT_MATCH"),
            ("lifetime_stale", a, b, "REJECT"),
        ):
            expected[(rep, key)] = expected_value
    if len(set(pixel_hashes)) != 1 or len(instance_ids) != 8 or len(server_pids) != 8 or len(fixture_pids) != 8 or len(xids) != 1:
        raise ValueError("cross-generation aggregate mismatch")

    seen = set()
    for row in raw["classification_rows"]:
        rep, policy, comparison = row.get("rep"), row.get("policy"), row.get("comparison")
        pair = next((p for p in raw["pairs"] if p["rep"] == rep), None)
        if pair is None or comparison not in ("same_generation", "cross_generation_stale"):
            raise ValueError("unknown pair/comparison")
        expected_source_token = pair["G1"]["server_instance_id"]
        expected_current_token = (expected_source_token if comparison == "same_generation"
                                  else pair["G2"]["server_instance_id"])
        if (row.get("source_server_instance_id") != expected_source_token
                or row.get("current_server_instance_id") != expected_current_token):
            raise ValueError("row lifetime-token binding mismatch")
        if policy == "CURRENT_TYPED":
            key = "current_fresh" if comparison == "same_generation" else "current_stale"
            computed = exact({"identity": pair["typed_identity_G1"],
                              "authority": "none", "task_input_granted": False,
                              "action_admission_eligible": False},
                             pair["typed_identity_G1" if comparison == "same_generation" else "typed_identity_G2"])
        elif policy == "LIFETIME_BOUND":
            key = "lifetime_fresh" if comparison == "same_generation" else "lifetime_stale"
            computed = "EXACT_MATCH" if comparison == "same_generation" else "REJECT"
        else:
            raise ValueError("unexpected policy")
        k = (rep, key)
        if k in seen or row.get("classification") != computed or row.get("classification") != expected.get(k):
            raise ValueError("row classification mismatch/duplicate")
        if row.get("authority") != "none" or row.get("task_input_granted") is not False or row.get("action_admission_eligible") is not False:
            raise ValueError("classification row authority mismatch")
        seen.add(k)
    if len(seen) != 16:
        raise ValueError("classification row set incomplete")

    for pair in raw["pairs"]:
        n = pair["negative_controls"]
        for k in ("missing_token", "forged_token"):
            control = n[k]
            recomputed = exact(control["receipt"], control["current_identity"])
            if (recomputed != "EXACT_MATCH" or control["source_token"] == control["current_token"]
                    or control["result"].get("classification") != "REJECT"):
                raise ValueError("lifetime token corruption not rejected: " + k)
        control = n["authority_escalation"]
        if (control["receipt"].get("task_input_granted") is not True
                or exact(control["receipt"], control["current_identity"]) != "INVALID"
                or control["result"].get("classification") != "INVALID"):
            raise ValueError("authority escalation control not invalid")
        for k in ("changed_backend", "changed_client_id", "known_transient_mismatch"):
            control = n[k]
            if (exact(control["receipt"], control["current_identity"]) not in ("MISMATCH", "INVALID")
                    or control["result"].get("classification") not in ("MISMATCH", "INVALID")):
                raise ValueError("typed identity corruption not rejected: " + k)
    raw_hash = sha(raw_bytes)
    sidecar = (root / "raw.sha256").read_text().split()[0]
    if raw_hash != sidecar:
        raise ValueError("raw sha256 sidecar mismatch")
    return {"audit": "PASS_INDEPENDENT_LIFETIME_RECONSTRUCTION",
            "disposition": "PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED",
            "pairs": 4, "classification_rows": 16, "negative_controls": 24,
            "xserver_lifetimes": 8, "xid_reused": next(iter(xids)),
            "pixels_identical": True, "input_calls": 0,
            "raw_sha256": raw_hash,
            "freeze_manifest_sha256": sha(freeze_bytes),
            "source_commit": freeze["source_commit"],
            "container_image_id": freeze["container_image_id"]}


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1])), sort_keys=True))
