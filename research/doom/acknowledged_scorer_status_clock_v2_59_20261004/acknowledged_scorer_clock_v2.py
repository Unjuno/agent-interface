"""Additive acknowledgment/metadata separation over scorer-status V1."""
import copy
import threading

from acknowledged_scorer_v1 import AcknowledgedProgressSample, AcknowledgedSampler


class AcknowledgedSamplerClockV2(AcknowledgedSampler):
    """Preserve returned-call fact when post-return clock/tic reads fail.

    An untimed producer is intentionally partial: it proves the client method
    returned, not an episode-tic advance or a usable observation interval.
    """

    def record_external_return_unqualified(self, game, before, started,
                                           returned=None, after=None):
        """Retain inner-call return when proxy clock/tic qualification fails."""
        self.before_external_update(game)
        self.update_sequence += 1
        producer = {"run_id": self.run_id,
                    "update_sequence": self.update_sequence,
                    "observation_status": ("UPDATE_RETURNED_UNTIMED" if returned is None
                                           else "UPDATE_RETURNED_UNBRACKETED"),
                    "tic_before": before, "update_started_ns": started}
        if returned is not None:
            producer["update_returned_ns"] = returned
        if after is not None:
            producer["tic_after"] = after
        self.external_ack = producer

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
        row = {"schema": "scorer-client-update-v1", "run_id": self.run_id,
               "sample_sequence": self.sequence, "controller_visible": False,
               "status": "UPDATE_UNAVAILABLE", "update_status": "NOT_ATTEMPTED",
               "sample_status": "NOT_ATTEMPTED"}
        producer = None
        external_before = self.external_ack
        try:
            if game.is_episode_finished():
                if self.last is not None and self.last.episode_finished:
                    producer = copy.deepcopy(self.last.producer)
                    producer.update(sample_sequence=self.sequence,
                                    observation_status="TERMINAL_REPEAT_NO_UPDATE")
                elif (self.external_ack is not None and
                      self.external_ack["tic_after"] == int(game.get_episode_time())):
                    producer = {**self.external_ack, "sample_sequence": self.sequence,
                                "observation_status": "EXTERNAL_UPDATE_RETURNED"}
                else:
                    raise RuntimeError("terminal state has no acknowledged sample")
                row["update_status"] = producer["observation_status"]
            else:
                before = int(game.get_episode_time())
                started = self.clock_ns()
                row.update(tic_before=before, update_started_ns=started)
                game.advance_action(1, True)
                if self.external_ack is not external_before:
                    # The V16 observed proxy already captured this update's
                    # timing and tic bracket. Reuse it; don't take a second,
                    # potentially conflicting clock measurement.
                    producer = {**self.external_ack,
                                "sample_sequence": self.sequence,
                                "observation_status": "UPDATE_RETURNED"}
                    row.update(status="UPDATE_RETURNED",
                               update_status="UPDATE_RETURNED",
                               tic_before=producer["tic_before"],
                               tic_after=producer["tic_after"],
                               update_started_ns=producer["update_started_ns"],
                               update_returned_ns=producer["update_returned_ns"])
                else:
                    # Set the API-return fact and identity before any fallible
                    # clock/tic qualification. Do not invent those measurements.
                    self.update_sequence += 1
                    row.update(status="UPDATE_METADATA_PENDING",
                               update_status="UPDATE_RETURNED")
                    producer = {"run_id": self.run_id,
                                "sample_sequence": self.sequence,
                                "update_sequence": self.update_sequence,
                                "observation_status": "UPDATE_RETURNED_UNTIMED",
                                "tic_before": before,
                                "update_started_ns": started}
                    row["producer"] = copy.deepcopy(producer)
                    returned = self.clock_ns()
                    after = int(game.get_episode_time())
                    row.update(update_returned_ns=returned, tic_after=after)
                    producer = {"run_id": self.run_id,
                                "sample_sequence": self.sequence,
                                "update_sequence": self.update_sequence,
                                "observation_status": "UPDATE_RETURNED",
                                "tic_before": before, "tic_after": after,
                                "update_started_ns": started,
                                "update_returned_ns": returned}
                row["producer"] = copy.deepcopy(producer)
                if producer["tic_after"] <= producer["tic_before"]:
                    raise RuntimeError("acknowledged update did not advance episode tic")

            row["producer"] = copy.deepcopy(producer)
            row["sample_status"] = "PENDING"
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
            if (producer is None and self.external_ack is not external_before and
                    self.external_ack.get("observation_status") in
                    ("UPDATE_RETURNED_UNTIMED", "UPDATE_RETURNED_UNBRACKETED")):
                producer = {**self.external_ack, "sample_sequence": self.sequence}
                row.update(status="UPDATE_METADATA_UNAVAILABLE",
                           update_status="UPDATE_RETURNED",
                           sample_status="NOT_ATTEMPTED",
                           producer=copy.deepcopy(producer))
            elif row["update_status"] == "NOT_ATTEMPTED":
                row.update(status="UPDATE_UNAVAILABLE",
                           update_status="UPDATE_UNAVAILABLE")
            elif row["sample_status"] == "PENDING":
                row.update(status="SAMPLE_UNAVAILABLE",
                           sample_status="UNAVAILABLE")
            elif (row["update_status"] == "UPDATE_RETURNED" and producer is not None
                  and producer.get("observation_status") == "UPDATE_RETURNED_UNTIMED"):
                row.update(status="UPDATE_METADATA_UNAVAILABLE")
            else:
                row["status"] = "UPDATE_VALIDATION_FAILED"
            row.update(error_type=type(error).__name__, error=str(error))
            raise
        finally:
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
