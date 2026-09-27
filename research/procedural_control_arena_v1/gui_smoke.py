from __future__ import annotations

from pathlib import Path
import tempfile
import tkinter as tk

from arena import ArenaApp
from engine import BenchmarkSession, EpisodeSpec, FULL_PRIMITIVES, generate_episode

spec = generate_episode(20260927, 0.6, suite='full')
by_kind = {s.kind: s for s in spec.stages}
assert set(by_kind) == set(FULL_PRIMITIVES)

for kind in FULL_PRIMITIVES:
    one = EpisodeSpec(spec.schema, spec.seed, spec.suite, spec.difficulty, (by_kind[kind],))
    session = BenchmarkSession(one)
    root = tk.Tk()
    root.withdraw()
    with tempfile.TemporaryDirectory() as td:
        app = ArenaApp(root, session, Path(td) / f'{kind}.json', 'fixed', None)
        app._render()
        root.update_idletasks()
        bbox = app.canvas.bbox('all')
        if not bbox:
            raise RuntimeError(f'empty render for {kind}')
        root.destroy()
print('GUI_SMOKE_PASS', len(FULL_PRIMITIVES))
