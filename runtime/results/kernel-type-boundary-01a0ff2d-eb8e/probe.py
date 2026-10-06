"""Ordinary type-boundary matrix; no backend or shared runtime mutation."""
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import platform
import sys
from types import SimpleNamespace

source_root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(source_root))
from runtime.kernel import EffectReceipt, EffectStatus, RequestLifecycle
from runtime.kernel.test_kernel import observation, binding, lease, request, execution, released, M, E


def encode(value):
    if isinstance(value, Enum):
        return {"type": type(value).__name__, "value": value.value}
    if is_dataclass(value):
        return {"type": type(value).__name__, "fields": {f.name: encode(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, SimpleNamespace):
        return {"type": "SimpleNamespace", "fields": {k: encode(v) for k, v in vars(value).items()}}
    if type(value) in (tuple, frozenset):
        encoded = [encode(v) for v in value]
        if type(value) is frozenset:
            encoded.sort(key=lambda x: json.dumps(x, sort_keys=True))
        return {"type": type(value).__name__, "items": encoded}
    if value is None or type(value) in (str, int, bool):
        return value
    return {"type": type(value).__name__}


def setup(n):
    flow = RequestLifecycle()
    if n >= 1: flow.record_observation(observation())
    if n >= 2: flow.bind(binding())
    if n >= 3: flow.authorize(lease(), now_ns=200)
    if n >= 4: flow.begin_execution(request(), now_ns=300)
    if n >= 5: flow.record_execution(execution())
    return flow


specs = [
    ("observation", 0, observation, {}, "record_observation", {}),
    ("binding", 1, binding, {"binding_digest": "bad"}, "bind", {}),
    ("authority", 2, lease, {"allowed_actions": frozenset()}, "authorize", {"now_ns": 200}),
    ("request", 3, request, {"actions": ()}, "begin_execution", {"now_ns": 300}),
    ("execution", 4, execution, {"ended_ns": 0}, "record_execution", {}),
    ("effect", 5, lambda: EffectReceipt("cmd-1", M, 900, EffectStatus.VERIFIED, E), {"evidence_digest": "bad"}, "record_effect", {}),
    ("stop", 4, released, {}, "stop", {}),
]
rows = []
for name, stage, factory, changes, method, kwargs in specs:
    for form in ("typed", "shape", "none", "unrelated"):
        flow = setup(stage)
        valid = factory()
        if form == "typed":
            supplied = valid
        elif form == "shape":
            data = {f.name: getattr(valid, f.name) for f in fields(valid)}
            data.update(changes)
            supplied = SimpleNamespace(**data) if name != "stop" else SimpleNamespace(released=True)
        elif form == "none":
            supplied = None
        else:
            supplied = object()
        before = {k: encode(v) for k, v in vars(flow).items()}
        error = None
        try:
            if method == "stop":
                flow.stop("cancelled", release=supplied)
            else:
                getattr(flow, method)(supplied, **kwargs)
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
        after = {k: encode(v) for k, v in vars(flow).items()}
        outcome = None
        if flow.stage.value in {"verified", "contradicted", "unavailable", "stopped"}:
            outcome = encode(flow.outcome())
        rows.append({"boundary": name, "form": form, "method": method,
                     "arguments": kwargs if name != "stop" else {"reason": "cancelled"},
                     "supplied": encode(supplied), "before": before, "after": after,
                     "exception": error, "outcome": outcome})
sources = {}
for path in sorted((source_root / "runtime/kernel").glob("*.py")):
    data = path.read_bytes()
    sources[path.relative_to(source_root).as_posix()] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
result = {"schema": "lifecycle-type-boundary-v1", "revision": sys.argv[2],
          "python": platform.python_version(), "platform": platform.platform(),
          "source_sha256": sources, "rows": rows}
destination = Path(sys.argv[3])
with destination.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps({"revision": sys.argv[2], "rows": len(rows), "destination": str(destination)}))
