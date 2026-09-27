"""Record moved scoped-X11 implementation bytes in new source manifests.

Read-only and deterministic; never imports the input implementation or rewrites
an existing experiment. This is a source snapshot, not an atomic execution pin.
"""
import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPERS = tuple('research/live_control/' + name + '.py' for name in (
    'coordinate_frame_transform_v1', 'scoped_target_handle_v1',
    'scoped_target_handle_v2', 'scoped_target_handle_v3',
    'native_handle_bridge_v1', 'native_guarded_form_v1'))
IMPLEMENTATIONS = tuple('runtime/guarded_x11_v1/' + name + '.py' for name in (
    '__init__', 'frames', 'handles_base', 'handles_texture', 'handles', 'bridge', 'form'))
HELPER = 'research/live_control/guarded_source_dependencies_v1.py'


def complete_guarded_hashes(hashes, *, base):
    """Preserve source keys and add the shared package plus this resolver.

    Keys keep the manifest's existing base convention. A frozen wrapper digest
    or conflicting implementation digest is refused, not upgraded in place.
    The whole shared package is pinned conservatively; this is not a general
    dependency resolver or a complete third-party/environment source manifest.
    """
    base = Path(base).resolve()
    root = ROOT.resolve()
    result = dict(hashes)
    paths = {name: (base / name).resolve() for name in hashes}
    wrappers = {root / name for name in WRAPPERS}
    selected = [name for name, path in paths.items() if path in wrappers]
    if not selected:
        return result
    for name in selected:
        actual = hashlib.sha256(paths[name].read_bytes()).hexdigest()
        if hashes[name] != actual:
            raise ValueError('wrapper source changed; create a fresh manifest: ' + name)
    for relative in (*IMPLEMENTATIONS, HELPER):
        path = root / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        aliases = [name for name, source in paths.items() if source == path]
        if any(hashes[name] != actual for name in aliases):
            raise ValueError('conflicting shared source digest: ' + relative)
        if not aliases:
            name = Path(os.path.relpath(path, base)).as_posix()
            result[name] = actual
    return result
