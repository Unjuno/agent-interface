from __future__ import annotations

from pathlib import Path
import tempfile
import tkinter as tk

from arena import ArenaApp
from engine import BenchmarkSession, EpisodeSpec, FULL_PRIMITIVES, generate_episode


FORBIDDEN_VISIBLE_TOKENS = (
    "move:",
    "target:",
    "wait",
    "switch:",
    "type:",
    "combo:",
    "drag:",
    "assemble",
    "trace:",
    "recovery:",
    "interrupted",
    "reacquire",
    "goal",
    "socket",
    "pieces",
    "ghost slots",
    "pass",
    "fail",
    "fingerprint",
    "stage ",
    "click terminal",
)


def visible_text(canvas: tk.Canvas) -> str:
    texts: list[str] = []
    for item in canvas.find_all():
        if canvas.type(item) == "text":
            text = canvas.itemcget(item, "text")
            if text:
                texts.append(text)
    return "\n".join(texts)


spec = generate_episode(20260927, 0.6, suite="full")
by_kind = {s.kind: s for s in spec.stages}
assert set(by_kind) == set(FULL_PRIMITIVES)

for kind in FULL_PRIMITIVES:
    one = EpisodeSpec(spec.schema, spec.seed, spec.suite, spec.difficulty, (by_kind[kind],))
    session = BenchmarkSession(one)
    root = tk.Tk()
    root.withdraw()
    with tempfile.TemporaryDirectory() as td:
        app = ArenaApp(root, session, Path(td) / f"{kind}.json", "fixed", None)
        app._render()
        root.update_idletasks()
        bbox = app.canvas.bbox("all")
        if not bbox:
            raise RuntimeError(f"empty render for {kind}")
        text = visible_text(app.canvas).lower()
        for token in FORBIDDEN_VISIBLE_TOKENS:
            if token in text:
                raise RuntimeError(f"policy/diagnostic leakage for {kind}: {token!r} in {text!r}")
        # TYPE must still expose task data (the code) without exposing a motor recipe.
        if kind == "typing" and str(by_kind[kind].payload["code"]).lower() not in text:
            raise RuntimeError("typing code missing from visible task state")
        root.destroy()

# Completion is neutral: scored outcome and diagnostic oracle remain report-only.
failure_spec = EpisodeSpec(spec.schema, spec.seed, spec.suite, spec.difficulty, (by_kind["target"],))
failure_session = BenchmarkSession(failure_spec)
failure_session.pointer_down(1, 1)
assert failure_session.done and not failure_session.success
root = tk.Tk()
root.withdraw()
with tempfile.TemporaryDirectory() as td:
    app = ArenaApp(root, failure_session, Path(td) / "failure.json", "fixed", None)
    app._render()
    root.update_idletasks()
    text = visible_text(app.canvas).lower()
    if "session complete" not in text:
        raise RuntimeError("neutral completion marker missing")
    for secret in ("fail", failure_session.failure_reason or "", failure_session.spec.public_fingerprint()):
        if secret and secret.lower() in text:
            raise RuntimeError(f"completion diagnostic leaked: {secret!r}")
    root.destroy()

print("GUI_SMOKE_PASS", len(FULL_PRIMITIVES))
