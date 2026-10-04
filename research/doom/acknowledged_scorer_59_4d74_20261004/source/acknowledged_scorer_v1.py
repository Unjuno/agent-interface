"""Opt-in client update provenance; not a live freshness qualification."""
from dataclasses import dataclass
import copy
import threading
import time
from independent_progress_clock_v2 import ProgressSample


@dataclass(frozen=True)
class AcknowledgedProgressSample(ProgressSample):
    producer: dict

    def as_dict(self):
        return {**super().as_dict(), "producer": copy.deepcopy(self.producer)}


class AcknowledgedSampler:
    def __init__(self, sample_fn, run_id, emit, clock_ns=time.perf_counter_ns):
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("nonempty run identity required")
        self.sample_fn = sample_fn
        self.run_id = run_id
        self.emit = emit
        self.clock_ns = clock_ns
        self.owner_thread = threading.get_ident()
        self.sequence = 0
        self.last = None
        self.game = None

    def __call__(self, game, variables, timeout_seconds, **kwargs):
        if threading.get_ident() != self.owner_thread:
            raise RuntimeError("scorer update left session main thread")
        if self.game is None:
            self.game = game
        elif self.game is not game:
            raise RuntimeError("new game requires a new scorer run")
        self.sequence += 1
        row = {"schema": "scorer-client-update-v1", "run_id": self.run_id,
               "sample_sequence": self.sequence, "controller_visible": False,
               "status": "UPDATE_UNAVAILABLE"}
        try:
            if game.is_episode_finished():
                if self.last is None or not self.last.episode_finished:
                    raise RuntimeError("terminal state has no acknowledged sample")
                # Terminal repeats carry the original acknowledgment explicitly.
                producer = copy.deepcopy(self.last.producer)
                producer.update(sample_sequence=self.sequence,
                                observation_status="TERMINAL_REPEAT_NO_UPDATE")
            else:
                before = int(game.get_episode_time())
                row.update(tic_before=before, update_started_ns=self.clock_ns())
                game.advance_action(1, True)
                row["update_returned_ns"] = self.clock_ns()
                after = int(game.get_episode_time())
                row["tic_after"] = after
                if after <= before:
                    raise RuntimeError("acknowledged update did not advance episode tic")
                producer = {"run_id": self.run_id, "sample_sequence": self.sequence,
                            "update_sequence": self.sequence,
                            "observation_status": "UPDATE_RETURNED",
                            "tic_before": before, "tic_after": after,
                            "update_started_ns": row["update_started_ns"],
                            "update_returned_ns": row["update_returned_ns"]}
            sample = self.sample_fn(game, variables, timeout_seconds, **kwargs)
            sample.validate()
            if int(game.get_episode_time()) != producer["tic_after"]:
                raise RuntimeError("episode tic changed across acknowledged sample")
            if sample.sample_ns < producer["update_returned_ns"]:
                raise RuntimeError("sample timestamp precedes update acknowledgment")
            if self.last is not None and sample.sample_ns <= self.last.sample_ns:
                raise RuntimeError("sample timestamp is not strictly increasing")
            result = AcknowledgedProgressSample(
                sample.sample_ns, sample.kill_count, sample.death_count,
                sample.episode_finished, sample.player_dead, sample.map_exit,
                producer)
            row.update(status=producer["observation_status"], sample=result.as_dict())
        except BaseException as error:
            row.update(status="UPDATE_UNAVAILABLE", error_type=type(error).__name__,
                       error=str(error))
            raise
        finally:
            # No retry after an ambiguous evidence-sink exception.
            self.emit(row)
        self.last = result
        return result
