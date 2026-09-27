"""Independent prefix-state contract; deliberately does not import policies."""


class PrefixOracle:
    def __init__(self, generation=1, target=1):
        self.generation = generation
        self.target = target
        self.revoked = set()
        self.previous = {}
        self.last_seq = {}
        self.stream_seq = 0
        self.actions = []

    def consume(self, event):
        kind = event.get("kind")
        seq = event.get("seq")
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
            self.generation, self.target = new_generation, new_target
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
        identity = (generation, event.get("target"))
        if identity != (self.generation, self.target) or generation in self.revoked:
            self.actions.append(("refuse", event.get("id", "")))
            return
        if seq <= self.last_seq.get(identity, 0):
            self.actions.append(("refuse", event.get("id", "")))
            return
        self.last_seq[identity] = seq
        value = event.get("value") is True
        was_true = self.previous.get(identity, False)
        self.previous[identity] = value
        if value and not was_true:
            self.actions.append(("emit", event.get("id", "")))


def snapshot(state):
    return {
        "generation": state.generation,
        "target": state.target,
        "revoked": sorted(state.revoked),
        "previous": sorted([[g, t, v] for (g, t), v in state.previous.items()]),
        "last_seq": sorted([[g, t, v] for (g, t), v in state.last_seq.items()]),
        "stream_seq": getattr(state, "stream_seq", None),
        "actions": [list(x) for x in state.actions],
    }
