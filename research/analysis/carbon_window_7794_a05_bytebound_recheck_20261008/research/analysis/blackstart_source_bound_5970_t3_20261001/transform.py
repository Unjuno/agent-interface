from __future__ import annotations

import difflib
import hashlib
import io
import json
import lzma
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "FREEZE.json"
SOURCE = HERE / "source"
DERIVED = HERE / "derived"
PREFIX = "research/integration/x11_reconnect_key_state_2107_v1/"


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"])


def reconstruct_sources() -> dict:
    freeze = json.loads(SPEC.read_text(encoding="utf-8"))
    commit = freeze["source_commit"]
    meta = json.loads(git_blob(commit, PREFIX + "EVIDENCE_BASE64.json"))
    if meta.get("archive_sha256") != freeze["archive_sha256"] or meta.get("archive_bytes") != freeze["archive_bytes"]:
        raise ValueError("FROZEN_ARCHIVE_METADATA_MISMATCH")
    chunks = []
    for part in meta["parts"]:
        encoded = git_blob(commit, PREFIX + part["path"]).decode("ascii").strip()
        digest = hashlib.sha256(encoded.encode("ascii")).hexdigest()
        if digest != freeze["archive_parts"].get(part["path"]) or digest != part["sha256"] or len(encoded) != part["chars"]:
            raise ValueError(f"ARCHIVE_PART_MISMATCH:{part['path']}")
        chunks.append(encoded)
    import base64
    archive = base64.b64decode("".join(chunks), validate=True)
    if len(archive) != freeze["archive_bytes"] or hashlib.sha256(archive).hexdigest() != freeze["archive_sha256"]:
        raise ValueError("FROZEN_ARCHIVE_HASH_MISMATCH")
    with tarfile.open(fileobj=io.BytesIO(lzma.decompress(archive)), mode="r:") as tar:
        members = {m.name: m for m in tar.getmembers() if m.isfile()}
        if len(members) != freeze["expanded_file_count"]:
            raise ValueError("FROZEN_INVENTORY_MISMATCH")
        case_count = sum("/formal_v2/" in name and name.endswith("/case.json") for name in members)
        if case_count != freeze["formal_case_count"]:
            raise ValueError("FROZEN_CASE_COUNT_MISMATCH")
        outputs = {}
        for name in ("app.py", "observer.py"):
            matches = [key for key in members if key.endswith("/source/" + name)]
            if len(matches) != 1:
                raise ValueError(f"FROZEN_SOURCE_MEMBER_MISMATCH:{name}:{len(matches)}")
            raw = tar.extractfile(members[matches[0]]).read()
            actual = hashlib.sha256(raw).hexdigest()
            if actual != freeze["source_hashes"][name]:
                raise ValueError(f"FROZEN_SOURCE_HASH_MISMATCH:{name}:{actual}")
            target = SOURCE / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            outputs[name] = {"archive_member": matches[0], "sha256": actual, "bytes": len(raw)}
    return {"archive_sha256": hashlib.sha256(archive).hexdigest(), "archive_bytes": len(archive),
            "expanded_file_count": len(members), "formal_case_count": case_count, "sources": outputs}


def replace_exact(text: str, old: str, new: str, label: str, expected_count: int = 1) -> str:
    count = text.count(old)
    if count != expected_count:
        raise ValueError(f"SOURCE_DRIFT:{label}:expected_{expected_count}_anchors_got_{count}")
    return text.replace(old, new, expected_count)


def transform_app(source: str) -> str:
    # Instrument only the archived callback; retain the original Tk app and event routing.
    source = replace_exact(
        source,
        "def ev(kind,e):\n    rec={'kind':kind,'keysym':e.keysym,'keycode':e.keycode,'state':e.state,'time':e.time,'mono_ns':time.monotonic_ns(),'value':var.get()}\n",
        "def ev(kind,e):\n    actions=json.loads(Path(sys.argv[2]).read_text())\n    act=actions['by_kind'][kind]\n    rec={'kind':kind,'keysym':e.keysym,'keycode':e.keycode,'state':e.state,'time':e.time,'mono_ns':time.monotonic_ns(),'value':var.get(),'source':'app','source_seq':act['seq'],'event_id':f\"app:{act['seq']}\",'actuation_id':act['actuation_id'],'causal_parent_ids':[f\"act:{act['actuation_id']}\"]}\n",
        "app_event_callback",
    )
    return source


def transform_observer(source: str) -> str:
    source = replace_exact(
        source,
        "fdx=d.fileno(); fdi=sys.stdin.fileno(); seq=0\n",
        "fdx=d.fileno(); fdi=sys.stdin.fileno(); seq=0\nact_path=sys.argv[4]\n",
        "observer_control_path",
    )
    source = replace_exact(
        source,
        "f.write(json.dumps({'seq':seq,'epoch':epoch,'kind':'KeyPress' if e.type==X.KeyPress else 'KeyRelease','detail':int(e.detail),'state':int(e.state),'time':int(e.time),'mono_ns':time.monotonic_ns()},sort_keys=True)+'\\n')",
        "kind='KeyPress' if e.type==X.KeyPress else 'KeyRelease'; act=json.load(open(act_path))['by_kind'][kind]; f.write(json.dumps({'seq':seq,'epoch':epoch,'kind':kind,'detail':int(e.detail),'state':int(e.state),'time':int(e.time),'mono_ns':time.monotonic_ns(),'source':'observer','source_seq':seq,'event_id':f\"observer:{epoch}:{seq}\",'actuation_id':act['actuation_id'],'causal_parent_ids':[f\"act:{act['actuation_id']}\"]},sort_keys=True)+'\\n')",
        "observer_event_callback",
        expected_count=2,
    )
    return source


def derive() -> dict:
    freeze = json.loads(SPEC.read_text(encoding="utf-8"))
    outputs = {}
    for name, fn in (("app.py", transform_app), ("observer.py", transform_observer)):
        raw = (SOURCE / name).read_bytes()
        expected = freeze["source_hashes"][name]
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError(f"SOURCE_HASH_MISMATCH:{name}:{actual}")
        transformed = fn(raw.decode("utf-8")).encode("utf-8")
        path = DERIVED / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(transformed)
        diff = "".join(difflib.unified_diff(raw.decode().splitlines(True), transformed.decode().splitlines(True), fromfile=f"archive/{name}", tofile=f"derived/{name}"))
        (DERIVED / f"{name}.diff").write_text(diff, encoding="utf-8")
        outputs[name] = {"source_sha256": actual, "derived_sha256": hashlib.sha256(transformed).hexdigest(), "diff_sha256": hashlib.sha256(diff.encode()).hexdigest()}
    return outputs


if __name__ == "__main__":
    print(json.dumps({"reconstruction": reconstruct_sources(), "derived": derive()}, sort_keys=True))
