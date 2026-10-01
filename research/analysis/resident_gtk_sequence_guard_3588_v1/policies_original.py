"""Candidate causal event policies for issue #3518 construction tests."""


class Resident:
    """Consume one event at a time; emitted effects cannot be erased later."""

    def __init__(self, generation=1, target=1):
        self.generation = generation
        self.target = target
        self.revoked = set()
        self.previous = {}
        self.last_seq = {}
        self.actions = []

    def step(self, event):
        kind = event["kind"]
        generation = event.get("gen", self.generation)
        if kind == "replace":
            self.generation = event["gen"]
            self.target = event["target"]
            self.actions.append(("invalidate", event["gen"], event["target"]))
            return
        if kind == "revoke":
            self.revoked.add(generation)
            self.actions.append(("release", generation))
            return
        if kind != "obs":
            return
        key = (generation, event.get("target"))
        seq = event["seq"]
        if key != (self.generation, self.target) or generation in self.revoked:
            self.actions.append(("refuse", event["id"]))
            return
        if seq <= self.last_seq.get(key, 0):
            self.actions.append(("refuse", event["id"]))
            return
        self.last_seq[key] = seq
        rising = event["value"] and not self.previous.get(key, False)
        self.previous[key] = event["value"]
        if rising:
            self.actions.append(("emit", event["id"]))


def last_message(events):
    """One decision for the final arrival: emit iff that message is true."""
    if not events:
        return []
    event = events[-1]
    return [event["id"]] if event.get("kind") == "obs" and event.get("value") else []


def message_count(events):
    """Emit once for every true observation arrival, including duplicates."""
    return [e["id"] for e in events if e.get("kind") == "obs" and e.get("value")]
