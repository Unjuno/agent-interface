"""Candidate asynchronous reobserve boundary for Issue #5413 T1."""
from dataclasses import dataclass, field


ALPHABET = ("INVALIDATE", "POLL", "OBS_MATCH", "OBS_UNLINKED", "OBS_REPLAY", "OBS_OLD_REQUEST", "ACT")


@dataclass
class State:
    generation: int = 0
    observation_seq: int = 0
    observed_generation: int = 0
    stale: bool = False
    pending_id: str | None = None
    pending_after_seq: int | None = None
    request_counter: int = 0
    superseded_id: str | None = None
    requests: list = field(default_factory=list)
    observations: list = field(default_factory=list)
    actions: list = field(default_factory=list)


def step(s, event):
    if event == "INVALIDATE":
        s.superseded_id = s.pending_id
        s.generation += 1
        s.stale = True
        s.observed_generation = -1
        s.pending_id = None
        s.pending_after_seq = None
    elif event == "POLL":
        if s.stale and s.pending_id is None:
            s.request_counter += 1
            s.pending_id = f"req-{s.request_counter}"
            s.pending_after_seq = s.observation_seq
            s.requests.append({"id": s.pending_id, "generation": s.generation,
                               "after_seq": s.pending_after_seq})
    elif event in {"OBS_MATCH", "OBS_UNLINKED", "OBS_REPLAY", "OBS_OLD_REQUEST"}:
        supplied_id, seq = s.pending_id, s.observation_seq + 1
        if event == "OBS_UNLINKED":
            supplied_id = None
        elif event == "OBS_REPLAY":
            seq = s.pending_after_seq if s.pending_after_seq is not None else s.observation_seq
        elif event == "OBS_OLD_REQUEST":
            supplied_id = s.superseded_id or "no-prior-request"
        linked = (s.pending_id is not None and supplied_id == s.pending_id
                  and s.pending_after_seq is not None and seq > s.pending_after_seq)
        s.observations.append({"event": event, "request_id": supplied_id,
                               "generation": s.generation, "seq": seq, "linked": linked})
        if linked:
            s.observation_seq = seq
            s.observed_generation = s.generation
            s.stale = False
            s.pending_id = None
            s.pending_after_seq = None
    elif event == "ACT":
        s.actions.append({"generation": s.generation,
                          "admitted": (not s.stale and s.observed_generation == s.generation)})
    else:
        raise ValueError("unknown event")


def execute_trace(trace):
    s = State()
    for event in trace:
        step(s, event)
    return {"trace": list(trace), "requests": s.requests,
            "observations": s.observations, "actions": s.actions,
            "final": {"generation": s.generation, "observation_seq": s.observation_seq,
                      "observed_generation": s.observed_generation, "stale": s.stale,
                      "pending_id": s.pending_id, "request_counter": s.request_counter}}
