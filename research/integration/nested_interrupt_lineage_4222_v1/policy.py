"""No I/O or scorer access. Completion matching produces eligibility only."""
FIELDS = ('session', 'id', 'generation', 'parent')

class Continuation:
    def __init__(self, frames, mode):
        if mode not in ('COUNT_ONLY_POP', 'LINEAGE_BOUND_POP'):
            raise ValueError(mode)
        self.stack = [dict(f) for f in frames]
        self.mode = mode
        self.emitted = False

    def deliver(self, receipt):
        before = [dict(f) for f in self.stack]
        accepted = bool(self.stack) and receipt.get('status') == 'RESOLVED'
        if self.mode == 'LINEAGE_BOUND_POP' and accepted:
            accepted = all(type(receipt.get(k)) is type(self.stack[-1][k]) and
                           receipt[k] == self.stack[-1][k] for k in FIELDS)
        if accepted:
            self.stack.pop()
        resume = accepted and not self.stack and not self.emitted
        if resume:
            self.emitted = True
        return dict(before=before, after=[dict(f) for f in self.stack],
                    accepted=accepted, resume=resume, authority=False)
