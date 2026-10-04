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
        self._failure = None
        self.external_ack = None
        self.update_sequence = 0
        self._ack_emit_failed = False

    def before_external_update(self, game):
        if self._failure is not None:
            raise RuntimeError("scorer failed; update retry refused") from self._failure
        if threading.get_ident() != self.owner_thread:
            raise RuntimeError("scorer update left session main thread")
        if self.game is None:
            self.game = game
        elif self.game is not game:
            raise RuntimeError("new game requires a new scorer run")

    def observe_external_update(self, game, before, after, started, returned):
        self.before_external_update(game)
        if after <= before or returned < started:
            raise RuntimeError("external update acknowledgment is unavailable")
        self.update_sequence += 1
        self.external_ack = {"run_id": self.run_id,
                             "update_sequence": self.update_sequence,
                             "tic_before": before, "tic_after": after,
                             "update_started_ns": started,
                             "update_returned_ns": returned}
        self._emit_ack(self.external_ack)

    def _emit_ack(self, producer):
        try:
            self.emit({"schema": "scorer-client-update-v2",
                   "event": "update_acknowledged", "run_id": self.run_id,
                   "update_sequence": producer["update_sequence"],
                   "tic_before": producer["tic_before"],
                   "tic_after": producer["tic_after"],
                   "update_started_ns": producer["update_started_ns"],
                   "update_returned_ns": producer["update_returned_ns"],
                   "update_status": "UPDATE_RETURNED",
                   "sample_status": "NOT_ATTEMPTED",
                   "producer": copy.deepcopy(producer)})
        except BaseException:
            self._ack_emit_failed = True
            raise

    def __call__(self, game, variables, timeout_seconds, **kwargs):
        if self._failure is not None:
            raise RuntimeError("scorer failed; update retry refused") from self._failure
        if threading.get_ident() != self.owner_thread:
            raise RuntimeError("scorer update left session main thread")
        if self.game is None:
            self.game = game
        elif self.game is not game:
            raise RuntimeError("new game requires a new scorer run")
        self.sequence += 1
        self._ack_emit_failed = False
        row = {"schema": "scorer-client-update-v2", "event": "sample_result", "run_id": self.run_id,
               "sample_sequence": self.sequence, "controller_visible": False,
               "status": "UPDATE_UNAVAILABLE",
               "update_status": "UPDATE_NOT_ATTEMPTED",
               "sample_status": "SAMPLE_NOT_ATTEMPTED"}
        try:
            if game.is_episode_finished():
                if self.last is not None and self.last.episode_finished:
                    # Terminal repeats carry the original acknowledgment explicitly.
                    producer = copy.deepcopy(self.last.producer)
                    producer.update(sample_sequence=self.sequence,
                                    observation_status="TERMINAL_REPEAT_NO_UPDATE")
                    row["update_status"] = "TERMINAL_REPEAT_NO_UPDATE"
                elif self.external_ack is not None and self.external_ack['tic_after'] == int(game.get_episode_time()):
                    producer = {**self.external_ack, "sample_sequence": self.sequence,
                                "observation_status": "EXTERNAL_UPDATE_RETURNED"}
                    row["update_status"] = "EXTERNAL_UPDATE_RETURNED"
                else:
                    raise RuntimeError("terminal state has no acknowledged sample")
            else:
                before = int(game.get_episode_time())
                row.update(update_status="UPDATE_IN_PROGRESS", tic_before=before,
                           update_started_ns=self.clock_ns())
                external_before = self.external_ack
                game.advance_action(1, True)
                row.update(update_status="UPDATE_RETURNED",
                           update_returned_ns=self.clock_ns())
                after = int(game.get_episode_time())
                row["tic_after"] = after
                if after <= before:
                    row["update_status"] = "UPDATE_RETURNED_NO_TIC_ADVANCE"
                    raise RuntimeError("acknowledged update did not advance episode tic")
                if self.external_ack is external_before:
                    self.update_sequence += 1
                producer = {"run_id": self.run_id, "sample_sequence": self.sequence,
                            "update_sequence": self.update_sequence,
                            "observation_status": "UPDATE_RETURNED",
                            "tic_before": before, "tic_after": after,
                            "update_started_ns": row["update_started_ns"],
                            "update_returned_ns": row["update_returned_ns"]}
                row["update_status"] = "UPDATE_RETURNED"
                if self.external_ack is external_before:
                    self._emit_ack(producer)
            row["producer"] = copy.deepcopy(producer)
            row["sample_status"] = "SAMPLE_IN_PROGRESS"
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
            row.update(status=producer["observation_status"],
                       sample_status="AVAILABLE", sample=result.as_dict())
        except BaseException as error:
            self._failure = error
            sample_started = row["sample_status"] == "SAMPLE_IN_PROGRESS"
            update_failed = row["update_status"] in {
                "UPDATE_NOT_ATTEMPTED", "UPDATE_IN_PROGRESS",
                "UPDATE_RETURNED_NO_TIC_ADVANCE",
            }
            if update_failed and row["update_status"] != "UPDATE_RETURNED_NO_TIC_ADVANCE":
                row["update_status"] = "UPDATE_UNAVAILABLE"
            update_unavailable = update_failed
            row.update(
                status="SAMPLE_UNAVAILABLE" if sample_started or "producer" in row or not update_unavailable
                else "UPDATE_UNAVAILABLE",
                sample_status="UNAVAILABLE" if sample_started
                else "NOT_ATTEMPTED",
                error_type=type(error).__name__, error=str(error))
            raise
        finally:
            # No retry after an ambiguous evidence-sink exception.
            if self._ack_emit_failed:
                raise self._failure
            try:
                self.emit(row)
            except BaseException as evidence_error:
                if self._failure is not None:
                    self._failure = BaseExceptionGroup(
                        "scorer sampling and evidence publication failed",
                        [self._failure, evidence_error])
                else:
                    self._failure = evidence_error
                raise self._failure
        self.last = result
        return result
