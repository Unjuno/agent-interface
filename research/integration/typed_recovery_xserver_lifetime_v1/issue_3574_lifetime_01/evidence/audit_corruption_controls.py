#!/usr/bin/env python3
"""Posthoc no-GUI integrity probes against copies of retained formal raw."""
import hashlib
import json
from pathlib import Path
import tempfile

import lifetime_audit

SOURCE = Path("/evidence")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mutate_denominator(raw):
    raw["classification_rows"].pop()


def mutate_xres_owner(raw):
    raw["pairs"][0]["G1"]["fixture"]["xres"]["rows"][0]["values"] = [999]


def mutate_pixels(raw):
    pixel = raw["pairs"][0]["G1"]["fixture"]["pixel_b64"]
    raw["pairs"][0]["G1"]["fixture"]["pixel_b64"] = ("A" if pixel[0] != "A" else "B") + pixel[1:]


def mutate_lifetime_token(raw):
    raw["classification_rows"][3]["current_server_instance_id"] = raw["classification_rows"][3]["source_server_instance_id"]


def mutate_input_authority(raw):
    raw["input_calls"] = 1


def mutate_cleanup(raw):
    raw["pairs"][0]["G1"]["cleanup"]["socket_disappeared"] = False


def mutate_manifest(raw):
    raw["freeze_manifest_sha256"] = "0" * 64


CASES = {
    "denominator": mutate_denominator,
    "xres-owner-pid": mutate_xres_owner,
    "pixel-bytes": mutate_pixels,
    "lifetime-token": mutate_lifetime_token,
    "input-authority": mutate_input_authority,
    "cleanup-socket": mutate_cleanup,
    "freeze-manifest": mutate_manifest,
}


def main():
    original = json.loads((SOURCE / "raw.json").read_text())
    results = []
    for name, mutation in CASES.items():
        with tempfile.TemporaryDirectory(prefix="audit-corruption-") as tmp:
            root = Path(tmp)
            row = json.loads(json.dumps(original))
            mutation(row)
            data = json.dumps(row, sort_keys=True, indent=2).encode()
            (root / "raw.json").write_bytes(data)
            (root / "raw.sha256").write_text(sha(data) + "  raw.json\n")
            try:
                lifetime_audit.audit(root)
            except Exception as error:
                results.append({"name": name, "detected": True, "error": repr(error)})
            else:
                results.append({"name": name, "detected": False, "error": None})
    print(json.dumps({"source_raw_sha256": sha((SOURCE / "raw.json").read_bytes()),
                      "controls": results,
                      "all_detected": all(x["detected"] for x in results)}, sort_keys=True))


if __name__ == "__main__":
    main()
