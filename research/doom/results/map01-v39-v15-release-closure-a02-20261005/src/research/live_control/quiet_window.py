"""Pixel quietness is a presentation hint, never semantic completion."""
class QuietWindow:
    def __init__(self, quiet_ns):
        self.quiet_ns=quiet_ns
        self.previous=None
        self.since=None

    def sample(self, value, now, focus_valid):
        if not focus_valid:
            self.previous=None;self.since=None
            return False
        if self.since is None or value!=self.previous:
            self.previous=value;self.since=now
            return False
        return now-self.since>=self.quiet_ns
