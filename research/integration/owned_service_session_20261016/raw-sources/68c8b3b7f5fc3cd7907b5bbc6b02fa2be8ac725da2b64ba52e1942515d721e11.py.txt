"""Recovery observation does not grant or refresh a program's input authority."""
from session_v6 import Backend as Previous, suite
from session_v4 import Backend as Operations
from executor_v3 import DecisionRequired


class Backend(Previous):
    def execute(self, step, cancel, identifier, index):
        # Bind once, even if the first step only observes. Later observations
        # must not silently authorize the tail of this same program.
        if not hasattr(cancel, 'expected_focus'):
            cancel.expected_focus = self.observed_focus
        if step['op'] not in ('observe', 'decide'):
            if cancel.expected_focus in (None, 0, 1) or getattr(cancel, 'focus_invalid', False):
                raise DecisionRequired()
        return Operations.execute(self, step, cancel, identifier, index)
