"""Explicit source closure for opt-in V39 per-key measurement."""
from pathlib import Path


def per_key_measurement_sources(doom_dir):
    root = Path(doom_dir)
    return (
        root / "map01_v39_perkey_bridge_a01" / "bridge.py",
        root / "map01_attack_onset_phase_allocation_02_v1" / "dependencies" / "v12" / "input_owner_v12.py",
        root.parent / "live_control" / "executor_v3.py",
    )


def with_per_key_measurement_sources(base_paths, doom_dir, enabled):
    paths = list(base_paths)
    helper_path = Path(__file__).resolve()
    if helper_path not in paths:
        paths.append(helper_path)
    if enabled:
        extra = per_key_measurement_sources(doom_dir)
        missing = [path for path in extra if not path.is_file()]
        if missing:
            raise FileNotFoundError("per-key measurement source closure is incomplete: " + ", ".join(map(str, missing)))
        paths.extend(extra)
    return paths
