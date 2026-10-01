"""Observation-only lifecycle comparison; NOT an action-admission policy."""
from copy import deepcopy
from predecessor import classify

AUTH = dict(authority="none", task_input_granted=False, action_admission_eligible=False)

class Tracker:
    """Local receive-order generation, not the X11 16-bit request sequence."""
    def __init__(self, epoch):
        self.epoch, self.ordinal, self.live, self.complete = epoch, 0, {}, True

    def feed(self, event):
        self.ordinal += 1
        if event.get("send_event"):
            self.complete = False
        wid = event["window"]
        if event["type"] == 16:  # CreateNotify, observed on root.
            if wid in self.live:
                self.complete = False
            self.live[wid] = self.ordinal
        elif event["type"] == 17:  # DestroyNotify.
            if wid not in self.live:
                self.complete = False
            self.live.pop(wid, None)

    def token(self, wid):
        if not self.complete or wid not in self.live:
            return None
        return dict(observer_epoch=self.epoch, create_ordinal=self.live[wid])


def receipt(capture):
    return {**AUTH, "identity": deepcopy(capture["identity"]),
            "process": deepcopy(capture["process"]),
            "lifecycle": deepcopy(capture["lifecycle"])}


def decisions(source, current, *, declared_gap=False):
    typed = classify(source, current["identity"])["classification"]
    process = typed
    if typed == "EXACT_MATCH":
        if not isinstance(source.get("process"), dict) or not isinstance(current.get("process"), dict):
            process = "UNKNOWN"
        elif source["process"] != current["process"]:
            process = "MISMATCH"
    life = process
    if process == "EXACT_MATCH":
        a, b = source.get("lifecycle"), current.get("lifecycle")
        def valid(x):
            return (isinstance(x, dict) and set(x) == {"observer_epoch", "create_ordinal"}
                    and isinstance(x["observer_epoch"], str) and bool(x["observer_epoch"])
                    and type(x["create_ordinal"]) is int and x["create_ordinal"] > 0)
        if declared_gap or not valid(a) or not valid(b):
            life = "UNKNOWN"
        elif a != b:
            life = "MISMATCH"
    return {"typed": typed, "process": process, "lifecycle": life}
