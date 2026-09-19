"""Finite semantic-selection identity successor for Issue #2018.
No GUI, model, network, or input calls.
"""
from dataclasses import dataclass
from itertools import product
import hashlib, json

@dataclass(frozen=True)
class Visual:
    pixels: str
    surface: str
    generation: int

@dataclass(frozen=True)
class Semantic:
    object_id: str | None
    surface: str
    generation: int
    available: bool = True

@dataclass(frozen=True)
class Observation:
    visual: Visual
    semantic: Semantic

def oracle(o: Observation, expected_surface: str, expected_generation: int):
    if not o.semantic.available:
        return "UNKNOWN"
    if o.visual.surface != expected_surface or o.semantic.surface != expected_surface:
        return "UNKNOWN"
    if o.visual.generation != expected_generation or o.semantic.generation != expected_generation:
        return "UNKNOWN"
    if o.semantic.object_id is None:
        return "UNKNOWN"
    return o.semantic.object_id

def visual_only(o: Observation):
    return "VISUAL_MATCH" if o.visual.pixels == "identical-selected" else "NO_MATCH"

def main():
    pixels = ("identical-selected", "different")
    surfaces = ("app-A", "app-B")
    generations = (1, 2)
    ids = ("obj-1", "obj-2", None)
    rows = []
    for px, vs, vg, ss, sg, oid, available in product(pixels, surfaces, generations, surfaces, generations, ids, (True, False)):
        o = Observation(Visual(px, vs, vg), Semantic(oid, ss, sg, available))
        expected = oracle(o, "app-A", 1)
        rows.append({"oracle": expected, "visual_only": visual_only(o),
                     "raw_sha": hashlib.sha256(json.dumps(o.__dict__, default=lambda x:x.__dict__, sort_keys=True).encode()).hexdigest()})
    assert len(rows) == 192
    # Pixel-identical replacement must remain distinguishable by semantic id.
    stable = Observation(Visual("identical-selected", "app-A", 1), Semantic("obj-1", "app-A", 1))
    replacement = Observation(Visual("identical-selected", "app-A", 1), Semantic("obj-2", "app-A", 1))
    assert oracle(stable, "app-A", 1) != oracle(replacement, "app-A", 1)
    # Unavailable, stale, cross-surface and missing semantic data never grant identity.
    for bad in (
        Observation(stable.visual, Semantic("obj-1", "app-A", 0)),
        Observation(stable.visual, Semantic("obj-1", "app-B", 1)),
        Observation(stable.visual, Semantic(None, "app-A", 1)),
        Observation(stable.visual, Semantic("obj-1", "app-A", 1, False)),
    ):
        assert oracle(bad, "app-A", 1) == "UNKNOWN"
    result = {"decision":"PASS_SEMANTIC_SELECTION_IDENTITY_FINITE_SCOPED", "rows":len(rows),
              "pixel_identical_replacement_distinguished":True, "unknown_fail_closed":True,
              "authority_events":0, "input_calls":0, "gui_calls":0, "model_calls":0, "network_calls":0}
    print(json.dumps(result, sort_keys=True))
    return result

if __name__ == "__main__":
    main()
