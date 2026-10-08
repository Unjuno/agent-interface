"""Sequence-monotone construction candidate for Issue #3588."""


class Resident:
    def __init__(self, generation=1, target=1):
        self.generation = generation
        self.target = target
        self.revoked = set()
        self.previous = {}
        self.last_seq = {}
        self.stream_seq = 0
        self.actions = []

    def step(self, event):
        kind = event.get("kind")
        seq = event.get("seq")
        event_id = event.get("id", "")
        if type(seq) is not int or seq <= self.stream_seq:
            self.actions.append(("refuse_control", kind, seq))
            return
        self.stream_seq = seq
        generation = event.get("gen", self.generation)
        if kind == "replace":
            new_generation = event.get("gen")
            new_target = event.get("target")
            if type(new_generation) is not int or new_generation <= self.generation or new_target is None:
                self.actions.append(("refuse_control", kind, seq))
                return
            self.generation = new_generation
            self.target = new_target
            self.actions.append(("invalidate", new_generation, new_target))
            return
        if kind == "revoke":
            if generation != self.generation:
                self.actions.append(("refuse_control", kind, seq))
                return
            self.revoked.add(generation)
            self.actions.append(("release", generation))
            return
        if kind != "obs":
            self.actions.append(("refuse_control", kind, seq))
            return
        key = (generation, event.get("target"))
        if key != (self.generation, self.target) or generation in self.revoked:
            self.actions.append(("refuse", event_id))
            return
        if seq <= self.last_seq.get(key, 0):
            self.actions.append(("refuse", event_id))
            return
        self.last_seq[key] = seq
        rising = event.get("value") is True and not self.previous.get(key, False)
        self.previous[key] = event.get("value") is True
        if rising:
            self.actions.append(("emit", event_id))


def last_message(events):
    if not events:
        return []
    event = events[-1]
    return [event["id"]] if event.get("kind") == "obs" and event.get("value") is True else []


def message_count(events):
    return [e["id"] for e in events if e.get("kind") == "obs" and e.get("value") is True]
