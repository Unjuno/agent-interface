"""One-shot deterministic composition probe for V39 invalidation and planner turns."""
import argparse
import json
import sys
from pathlib import Path

# This file is under research/doom/<package>; parents[3] is repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.doom.map01_overlap_controller_v39 import cancel_invalidated_cover
from research.live_control.persistent_planner_adapter_v2 import PersistentPlannerAdapter


SCHEMA = {"type": "object", "properties": {"action": {"type": "string"}},
          "required": ["action"], "additionalProperties": False}


def answer(label):
    return {"status": "completed", "items": [{"type": "agentMessage",
                                                  "text": json.dumps({"action": label})}]}


class Client:
    def __init__(self, *, interrupt_fails=False):
        self.events = []
        self.turn = 0
        self.interrupt_fails = interrupt_fails

    def start_thread(self, **kwargs):
        self.events.append({"event": "thread_started", "thread_id": "thread-1"})
        return {"thread": {"id": "thread-1"}}

    def start_turn(self, thread_id, inputs, **kwargs):
        self.turn += 1
        turn_id = f"turn-{self.turn}"
        self.events.append({"event": "turn_started", "thread_id": thread_id,
                            "turn_id": turn_id, "input": inputs[0]["text"]})
        return {"turn": {"id": turn_id}}

    def interrupt_turn(self, thread_id, turn_id):
        self.events.append({"event": "planner_interrupt", "thread_id": thread_id,
                            "turn_id": turn_id})
        if self.interrupt_fails:
            raise OSError("synthetic interrupt transport error")
        return {"accepted": True}

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        self.events.append({"event": "turn_answer_arrived", "thread_id": thread_id,
                            "turn_id": turn_id})
        return {"threadId": thread_id,
                "turn": {"id": turn_id, **answer("stale" if turn_id == "turn-1" else "fresh")}}

    def latest_turn_usage(self, thread_id, turn_id):
        return None

    def close(self, timeout=5):
        self.events.append({"event": "client_closed"})


class Pipe:
    def __init__(self, events):
        self.events = events

    def write(self, value):
        row = json.loads(value)
        self.events.append({"event": "cover_cancel", **row})

    def flush(self):
        pass


class Process:
    def __init__(self, events):
        self.stdin = Pipe(events)


def terminal(status="cancelled", release=None):
    if release is None:
        release = {"verified": True, "keys_down": [], "buttons_down": []}
    return {"event": "terminal", "id": "cover-1", "status": status,
            "release": release}


def run_case(name, *, status="cancelled", release=None, interrupt_fails=False,
             should_accept=False):
    client = Client(interrupt_fails=interrupt_fails)
    planner = PersistentPlannerAdapter(
        client, model="fixed-test-model", effort="low", cwd="/repo",
        base_instructions="Return JSON only.")
    planner.start_session()
    handle = planner.begin_turn("old observation", output_schema=SCHEMA)
    term = terminal(status, release)
    try:
        interrupt, observed = cancel_invalidated_cover(
            planner, handle, Process(client.events), lambda predicate: term, "cover-1")
        disposition = "accepted"
    except RuntimeError as error:
        interrupt = {"outcome": "request_error" if interrupt_fails else "requested"}
        observed = term
        disposition = "rejected"
        client.events.append({"event": "terminal_rejected", "reason": str(error)})
    client.events.append({"event": "interrupt_outcome", "outcome": interrupt["outcome"]})
    client.events.append({"event": "cover_terminal", "status": observed["status"],
                          "release": observed.get("release")})
    old = planner.await_turn(handle)
    client.events.append({"event": "old_turn_result", "status": old.status,
                          "answer_eligible": old.answer_eligible,
                          "answer": old.answer})
    fresh = None
    if should_accept:
        next_handle = planner.begin_turn("fresh observation", output_schema=SCHEMA)
        fresh_result = planner.await_turn(next_handle)
        fresh = {"thread_id": next_handle.thread_id,
                 "answer_eligible": fresh_result.answer_eligible,
                 "answer": fresh_result.answer}
        client.events.append({"event": "fresh_turn_result", **fresh})
    return {"case": name, "status": status, "release": term.get("release"),
            "interrupt_fails": interrupt_fails, "disposition": disposition,
            "expected_accept": should_accept, "interrupt_outcome": interrupt["outcome"],
            "old_answer_eligible": old.answer_eligible, "old_answer": old.answer,
            "fresh_result": fresh, "events": client.events}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    cases = [
        run_case("cancelled-empty", should_accept=True),
        run_case("completed-empty-race", status="completed", should_accept=True),
        run_case("expired-empty-race", status="expired", should_accept=True),
        run_case("interrupt-transport-error", interrupt_fails=True, should_accept=True),
        run_case("failed-terminal", status="failed"),
        run_case("needs-decision-terminal", status="needs_decision"),
        run_case("missing-release", release={}),
        run_case("unverified-release", release={"verified": False, "keys_down": [], "buttons_down": []}),
        run_case("held-key-release", release={"verified": True, "keys_down": ["space"], "buttons_down": []}),
        run_case("held-button-release", release={"verified": True, "keys_down": [], "buttons_down": ["left"]}),
    ]
    result = {"format": "v39-interrupt-cancel-composition-a02-v1",
              "source_main": "f72cd82d62c9d9f3860d4fa40980c56618bf5aaf",
              "cases": cases}
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"candidate cases={len(cases)} output={path} (created exclusively; no overwrite)")


if __name__ == "__main__":
    main()
