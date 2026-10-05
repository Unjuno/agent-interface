"""Optional conservative keymap brackets; never evidence of application input.

The A01 field names are retained for the existing projection. The version and
interval basis distinguish individual DOWN samples from correlated batch UP
samples, and per-key emergency cleanup observations. This recorder owns no input authority and runs on the owner thread.
"""


class KeyEdgeMeasurements:
    def __init__(self, owner_id):
        self.owner_id = owner_id
        self.generation = 0
        self.active = {}

    def forget(self, code):
        self.active.pop(code, None)

    def clear(self):
        # Cleanup may have acted without a pairable explicit UP measurement.
        self.active.clear()

    def edge(self, edge, code, key, token, pre, post, request_ns, sync_ns,
             *, owned_before=False, operation_ok=True, batch_id=None,
             post_sample_basis=None, cleanup=False):
        previous = self.active.pop(code, None)
        expected_pre, expected_post = (False, True) if edge == "down" else (True, False)
        confirmed = (
            operation_ok and isinstance(token, str) and bool(token)
            and pre["available"] is True and post["available"] is True
            and pre["error"] is None and post["error"] is None
            and pre["down"] is expected_pre and post["down"] is expected_post
            and all(type(n) is int for n in
                    (pre["started_ns"], pre["finished_ns"], request_ns,
                     sync_ns, post["started_ns"], post["finished_ns"]))
            and pre["started_ns"] <= pre["finished_ns"] <= request_ns
            <= sync_ns <= post["started_ns"] <= post["finished_ns"]
        )
        identity = None
        if edge == "down":
            confirmed = confirmed and not owned_before and previous is None
            if confirmed:
                self.generation += 1
                identity = f"{self.owner_id}:{self.generation}"
                self.active[code] = (key, token, identity)
        else:
            confirmed = confirmed and previous is not None and previous[:2] == (key, token)
            if confirmed:
                identity = previous[2]
        status = ("CONFIRMED_PHYSICAL_" + edge.upper() if confirmed
                  else "KEYMAP_EDGE_UNCONFIRMED")
        basis = ("key_snapshot" if edge == "down" else
                 "per_key_cleanup_snapshot" if cleanup else "shared_batch_snapshot")
        interval = [pre["finished_ns"], post["finished_ns"]] if confirmed else None
        common = dict(owner_id=self.owner_id, intent_token=token, key=key,
                      grants_input_authority=False, application_consumption_observed=False)
        bracket = dict(common, status=status, actuation_id=identity, **{f"physical_{edge}_interval": interval}) if confirmed else None
        adapter = dict(common, edge=edge, status=status, actuation_id=identity,
                       interval=interval) if confirmed else None
        return dict(common, schema="keymap-batch-edge-v1", interval_basis=basis,
                    scope="conservative X-server keymap observation bracket; no physical dwell or application receipt",
                    edge=edge, classification=status, bracket=bracket,
                    actuation_id=identity,
                    identity_status=("MINTED" if edge == "down" else "RETIRED") if confirmed else "UNAVAILABLE",
                    pre_sample=pre, post_sample=post,
                    **{("press_request_ns" if edge == "down" else "release_request_ns"): request_ns},
                    sync_return_ns=sync_ns, release_attempted=edge == "up",
                    adapter_edge=adapter, batch_id=batch_id, post_sample_basis=post_sample_basis)


def key_sample(bitmap, error, started_ns, finished_ns, code):
    return dict(available=bitmap is not None and error is None,
                down=bool(bitmap[code // 8] & (1 << (code % 8))) if bitmap is not None else None,
                started_ns=started_ns, finished_ns=finished_ns, error=error)
