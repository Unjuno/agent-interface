from __future__ import annotations
from dataclasses import dataclass
from typing import Any

VALID_ROLES={"ADMISSION_DEPENDENCY","PLANNER_CONTEXT","EFFECT_EVIDENCE","INVALIDATOR"}

@dataclass(frozen=True)
class Source:
    source_id: str
    source_kind: str
    context: str
    timestamp_ns: int
    currentness: str
    evidence_role: str
    provenance: str
    payload_ref: str

    def item(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "context": self.context,
            "timestamp_ns": self.timestamp_ns,
            "currentness": self.currentness,
            "evidence_role": self.evidence_role,
            "provenance": self.provenance,
            "payload_ref": self.payload_ref,
        }

SOURCES={
 "frame_current":Source("frame_current","PIXELS","game",1000,"CURRENT","ADMISSION_DEPENDENCY","capture://game/1000","payload://frame-current"),
 "engine_pose":Source("engine_pose","ENGINE_STATE","game",1000,"CURRENT","PLANNER_CONTEXT","engine://pose/1000","payload://engine-pose"),
 "test_failure":Source("test_failure","TEST","repo",2000,"CURRENT","PLANNER_CONTEXT","test://failure/2000","payload://test-failure"),
 "runtime_log":Source("runtime_log","LOG","repo",1990,"CURRENT","PLANNER_CONTEXT","log://runtime/1990","payload://runtime-log"),
 "source_fn":Source("source_fn","CODE","repo",1500,"HISTORICAL","PLANNER_CONTEXT","git://source-fn/revA","payload://source-fn"),
 "env_secret":Source("env_secret","ENV_SECRET","repo",2000,"CURRENT","PLANNER_CONTEXT","env://secret","payload://secret"),
 "viewport":Source("viewport","VIEWPORT","blender",3000,"CURRENT","PLANNER_CONTEXT","capture://viewport/3000","payload://viewport"),
 "scene_graph":Source("scene_graph","SCENE_GRAPH","blender",3000,"CURRENT","PLANNER_CONTEXT","scene://graph/3000","payload://scene-graph"),
 "renderer_debug":Source("renderer_debug","RENDERER_DEBUG","blender",3000,"CURRENT","PLANNER_CONTEXT","renderer://debug/3000","payload://renderer-debug"),
 "window_a":Source("window_a","PIXELS","windowA",4000,"CURRENT","PLANNER_CONTEXT","capture://windowA/4000","payload://window-a"),
 "window_b":Source("window_b","PIXELS","windowB",4000,"CURRENT","PLANNER_CONTEXT","capture://windowB/4000","payload://window-b"),
 "window_c":Source("window_c","PIXELS","windowC",4000,"CURRENT","PLANNER_CONTEXT","capture://windowC/4000","payload://window-c"),
 "desktop_frame":Source("desktop_frame","PIXELS","desktop",5000,"CURRENT","ADMISSION_DEPENDENCY","capture://desktop/5000","payload://desktop-frame"),
 "effect_event":Source("effect_event","EVENT","desktop",4990,"CURRENT","EFFECT_EVIDENCE","event://effect/4990","payload://effect-event"),
 "desktop_log":Source("desktop_log","LOG","desktop",4980,"CURRENT","PLANNER_CONTEXT","log://desktop/4980","payload://desktop-log"),
}

def ordered(case):
    return sorted(case["requested"], key=lambda sid:(-case["scores"].get(sid,-1),sid))

def compile_relevance_only(case):
    unsupported=[]; known=[]
    for sid in ordered(case):
        if sid not in SOURCES: unsupported.append(sid)
        else: known.append(sid)
    included=known[:case["max_items"]]
    omitted=known[case["max_items"]:]
    return {
      "policy":"RELEVANCE_ONLY",
      "items":[SOURCES[s].item() for s in included],
      "included_ids":included,
      "rejected_disallowed":[],
      "omitted_due_to_budget":omitted,
      "unsupported_sources":unsupported,
    }

def compile_capability_gated(case):
    unsupported=[]; rejected=[]; allowed=[]
    kinds=set(case["allowed_kinds"]); contexts=set(case["allowed_contexts"])
    for sid in ordered(case):
        if sid not in SOURCES:
            unsupported.append(sid); continue
        src=SOURCES[sid]
        if src.source_kind not in kinds or src.context not in contexts:
            rejected.append(sid); continue
        allowed.append(sid)
    included=allowed[:case["max_items"]]
    omitted=allowed[case["max_items"]:]
    return {
      "policy":"CAPABILITY_GATED",
      "items":[SOURCES[s].item() for s in included],
      "included_ids":included,
      "rejected_disallowed":rejected,
      "omitted_due_to_budget":omitted,
      "unsupported_sources":unsupported,
    }

def validate_presentation(raw):
    for field in ("source_id","provenance","evidence_role","currentness"):
        if not raw.get(field): return False,f"MISSING_{field.upper()}"
    if raw["evidence_role"] not in VALID_ROLES: return False,"UNKNOWN_EVIDENCE_ROLE"
    if raw.get("presentation_role_override") is not None: return False,"ROLE_OVERRIDE_FORBIDDEN"
    if raw.get("presentation_currentness_override") is not None: return False,"CURRENTNESS_OVERRIDE_FORBIDDEN"
    return True,"VALID"
