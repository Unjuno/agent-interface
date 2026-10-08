"""Candidate transition system for Issue #5413 causal reobserve T0."""
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
    last_request_id: str | None = None
    superseded_id: str | None = None
    requests: list = field(default_factory=list)
    observations: list = field(default_factory=list)
    actions: list = field(default_factory=list)


def step(state, symbol):
    if symbol == "INVALIDATE":
        state.superseded_id = state.pending_id
        state.generation += 1
        state.stale = True
        state.observed_generation = -1
        state.pending_id = None
        state.pending_after_seq = None
    elif symbol == "POLL":
        if state.stale and state.pending_id is None:
            state.request_counter += 1
            state.pending_id = f"req-{state.request_counter}"
            state.pending_after_seq = state.observation_seq
            state.last_request_id = state.pending_id
            state.requests.append({"id": state.pending_id, "generation": state.generation,
                                   "after_seq": state.pending_after_seq})
    elif symbol in {"OBS_MATCH", "OBS_UNLINKED", "OBS_REPLAY", "OBS_OLD_REQUEST"}:
        request_id = state.pending_id
        generation = state.generation
        seq = state.observation_seq + 1
        if symbol == "OBS_UNLINKED":
            request_id = None
        elif symbol == "OBS_REPLAY":
            seq = state.pending_after_seq if state.pending_after_seq is not None else state.observation_seq
        elif symbol == "OBS_OLD_REQUEST":
            request_id = state.superseded_id or "superseded-request"
        linked = (state.pending_id is not None and request_id == state.pending_id
                  and generation == state.generation and state.pending_after_seq is not None
                  and seq > state.pending_after_seq)
        state.observations.append({"event": symbol, "request_id": request_id,
                                   "generation": generation, "seq": seq, "linked": linked})
        if linked:
            state.observation_seq = seq
            state.observed_generation = generation
            state.stale = False
            state.pending_id = None
            state.pending_after_seq = None
    elif symbol == "ACT":
        admitted = not state.stale and state.observed_generation == state.generation
        state.actions.append({"generation": state.generation, "admitted": admitted})
    else:
        raise ValueError("unknown event")
    return state


def execute_trace(trace):
    state = State()
    for symbol in trace:
        step(state, symbol)
    return {"trace": list(trace), "requests": state.requests,
            "observations": state.observations, "actions": state.actions,
            "final": {"generation": state.generation, "observation_seq": state.observation_seq,
                      "observed_generation": state.observed_generation, "stale": state.stale,
                      "pending_id": state.pending_id, "request_counter": state.request_counter}}
