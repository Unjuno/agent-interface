from dataclasses import dataclass, field

@dataclass
class Case:
    op: str
    key_available: bool
    fault: bool
    active_relation: str
    focus_invalid: bool
    lease_ok: bool
    cancel: bool
    held_relation: str
    physical_down: bool
    inject_ok: bool
    sync_ok: bool
    sample_pre_ok: bool
    sample_post_ok: bool

@dataclass
class State:
    revision: int = 0
    active_relation: str = "none"
    active_pointer: bool = False
    held_relation: str = "none"
    touched: bool = False
    physical_down: bool = False
    trace: list = field(default_factory=list)

class Outcome:
    def __init__(self, ok, result=None, error=None):
        self.ok=ok; self.result=result; self.error=error
    def semantic(self):
        return (self.ok, self.result, self.error)

def execute(case: Case):
    s=State(active_relation=case.active_relation, held_relation=case.held_relation, physical_down=case.physical_down)
    try:
        s.revision += 1; s.trace.append(("revision", s.revision))
        s.trace.append(("key_lookup", case.key_available))
        if not case.key_available:
            raise ValueError("key unavailable on input owner")
        if case.op == "down":
            s.trace.append(("fault_check", case.fault))
            if case.fault: raise RuntimeError("input owner failed closed")
            s.trace.append(("active_check", case.active_relation))
            if case.active_relation == "other": raise ValueError("another intent owns input")
            s.trace.append(("focus_check", case.focus_invalid))
            if case.focus_invalid: raise RuntimeError("DecisionRequired")
            s.trace.append(("lease_check", case.lease_ok))
            if not case.lease_ok: raise RuntimeError("lease check failed")
            s.trace.append(("cancel_check", case.cancel))
            if case.cancel: raise RuntimeError("Cancelled")
            s.trace.append(("admitted_clock",))
            s.active_relation = "self"; s.trace.append(("set_active", "self"))
            s.active_pointer = False; s.trace.append(("set_active_pointer", False))
            s.touched = True; s.trace.append(("touched_add",))
            s.held_relation = "self"; s.trace.append(("held_set", "self"))
            s.trace.append(("KeyPress",))
            if not case.inject_ok: raise RuntimeError("inject failed")
            s.physical_down = True
            s.trace.append(("sync",))
            if not case.sync_ok: raise RuntimeError("sync failed")
            s.trace.append(("input_ack_clock",))
            return s, Outcome(True, "input_admission")
        elif case.op == "up":
            s.trace.append(("held_owner_check", case.held_relation))
            if case.held_relation == "other": raise ValueError("key belongs to another intent")
            if case.held_relation == "self":
                s.trace.append(("KeyRelease",))
                if not case.inject_ok: raise RuntimeError("inject failed")
                s.physical_down = False
                s.trace.append(("sync",))
                if not case.sync_ok: raise RuntimeError("sync failed")
                s.held_relation = "none"; s.trace.append(("held_del",))
            return s, Outcome(True, None)
        else:
            raise ValueError("bad op")
    except Exception as exc:
        return s, Outcome(False, error=f"{type(exc).__name__}:{exc}")
