"""Additive update/sample status separation; synthetic/local evidence only."""
import copy
import threading
import time

from independent_progress_clock_v2 import ProgressSample


class AcknowledgedProgressSampleV2(ProgressSample):
    def __init__(self, *args, producer):
        super().__init__(*args)
        self.producer = copy.deepcopy(producer)

    def as_dict(self):
        return {**super().as_dict(), "producer": copy.deepcopy(self.producer)}


class AcknowledgedSamplerV2:
    """Record client-update acknowledgment separately from scorer availability.

    Each call emits an update_acknowledged event (when an update returns and
    advances the tic), followed by exactly one sample_result event. Once any
    operation or sink fails, this run is latched and cannot be retried.
    """

    def __init__(self, sample_fn, run_id, emit, clock_ns=time.perf_counter_ns):
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("nonempty run identity required")
        self.sample_fn, self.run_id, self.emit = sample_fn, run_id, emit
        self.clock_ns = clock_ns
        self.owner_thread = threading.get_ident()
        self.sequence = 0
        self.update_sequence = 0
        self.game = None
        self.last = None
        self._failure = None

    def _check(self, game):
        if self._failure is not None:
            raise RuntimeError("scorer failed; retry refused") from self._failure
        if threading.get_ident() != self.owner_thread:
            raise RuntimeError("scorer update left session main thread")
        if self.game is None:
            self.game = game
        elif self.game is not game:
            raise RuntimeError("new game requires a new scorer run")

    def _emit(self, event):
        try:
            self.emit(event)
        except BaseException as error:
            self._failure = error
            raise

    def __call__(self, game, variables, timeout_seconds, **kwargs):
        self._check(game)
        self.sequence += 1
        base = {"schema": "scorer-client-update-v2", "run_id": self.run_id,
                "sample_sequence": self.sequence, "controller_visible": False}
        producer = None
        sample_started = False
        try:
            if game.is_episode_finished():
                if self.last is None or not self.last.episode_finished:
                    raise RuntimeError("terminal state has no acknowledged sample")
                producer = copy.deepcopy(self.last.producer)
                producer.update(sample_sequence=self.sequence,
                                observation_status="TERMINAL_REPEAT_NO_UPDATE")
            else:
                before = int(game.get_episode_time())
                started = self.clock_ns()
                game.advance_action(1, True)
                returned = self.clock_ns()
                after = int(game.get_episode_time())
                if after <= before:
                    raise RuntimeError("acknowledged update did not advance episode tic")
                self.update_sequence += 1
                producer = {"run_id": self.run_id, "sample_sequence": self.sequence,
                            "update_sequence": self.update_sequence,
                            "observation_status": "UPDATE_RETURNED", "tic_before": before,
                            "tic_after": after, "update_started_ns": started,
                            "update_returned_ns": returned}
                self._emit({**base, "event": "update_acknowledged",
                            "update_status": "UPDATE_RETURNED", "producer": producer})

            sample_started = True
            sample = self.sample_fn(game, variables, timeout_seconds, **kwargs)
            sample.validate()
            if int(game.get_episode_time()) != producer["tic_after"]:
                raise RuntimeError("episode tic changed across acknowledged sample")
            if sample.sample_ns < producer["update_returned_ns"]:
                raise RuntimeError("sample timestamp precedes update acknowledgment")
            if self.last is not None and sample.sample_ns <= self.last.sample_ns:
                raise RuntimeError("sample timestamp is not strictly increasing")
            result = AcknowledgedProgressSampleV2(
                sample.sample_ns, sample.kill_count, sample.death_count,
                sample.episode_finished, sample.player_dead, sample.map_exit,
                producer=producer)
        except BaseException as error:
            # A sink failure has an ambiguous commit outcome. _emit latched
            # this exact exception; do not publish a second status row.
            if self._failure is error:
                raise
            self._failure = error
            event = {**base, "event": "sample_result",
                     "update_status": "UPDATE_RETURNED" if producer else "UPDATE_UNAVAILABLE",
                     "sample_status": "UNAVAILABLE" if sample_started else "NOT_ATTEMPTED",
                     "error_type": type(error).__name__, "error": str(error)}
            if producer is not None:
                event["producer"] = producer
            try:
                self._emit(event)
            except BaseException as evidence_error:
                combined = BaseExceptionGroup(
                    "scorer sampling and evidence publication failed",
                    [error, evidence_error])
                self._failure = combined
                raise combined
            raise
        self._emit({**base, "event": "sample_result",
                    "update_status": "UPDATE_RETURNED" if producer["observation_status"] == "UPDATE_RETURNED" else producer["observation_status"],
                    "sample_status": "AVAILABLE", "producer": producer,
                    "sample": result.as_dict()})
        self.last = result
        return result
