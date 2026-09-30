"""Read exact evidence blobs captured at the frozen main commit."""

import json
import hashlib
import pathlib
import subprocess

BASE_COMMIT = "6968d45197c6a29e717a9281dcd050be1eed90c7"
SOURCES = {
    "physical": ("research/doom/map01_v12_physical_occupancy_live_r1_v1/FORMAL_RESULT.json", "0ddf43cbfec7957f1c51e6260dfca572463b3c6f"),
    "occupancy": ("research/doom/map01_held_input_occupancy_partial_posthoc_v2/RESULT_SUMMARY.json", "64ae125866a8e58f6deb90c8433506577ccd0a95"),
    "feedback": ("research/doom/map01_first_useful_feedback_posthoc_v1/result_summary.json", "bfdcd8c299a7dbe759977b346737bf592e3f4772"),
    "calc": ("runtime/results/calc-final-wait-01/RESULT.json", "11c4a4c78f9abffe44ca29182bfad38646307500"),
}


def load_inputs(repository_path):
    repository = pathlib.Path(repository_path).resolve()
    inputs = {}
    provenance = {"base_commit": BASE_COMMIT, "sources": {}}
    for name, (source_path, blob) in SOURCES.items():
        raw = subprocess.run(
            ["git", "cat-file", "blob", blob],
            cwd=repository,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        inputs[name] = json.loads(raw)
        provenance["sources"][name] = {"path": source_path, "blob": blob}
    return inputs, provenance


def load_inputs_from_payload(payload):
    """Validate host-exported UTF-8 blob contents and parse them in-container."""
    envelope = json.loads(payload)
    if envelope.get("base_commit") != BASE_COMMIT:
        raise ValueError("base commit mismatch")
    supplied = envelope.get("sources", {})
    if set(supplied) != set(SOURCES):
        raise ValueError("source set mismatch")
    inputs = {}
    provenance = {"base_commit": BASE_COMMIT, "sources": {}}
    for name, (source_path, expected_blob) in SOURCES.items():
        raw = supplied[name].encode("utf-8")
        actual_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        if actual_blob != expected_blob:
            raise ValueError("blob hash mismatch:" + name)
        inputs[name] = json.loads(raw)
        provenance["sources"][name] = {"path": source_path, "blob": actual_blob}
    return inputs, provenance
