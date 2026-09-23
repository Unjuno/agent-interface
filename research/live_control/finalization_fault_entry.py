"""Test-only one-shot failures around the actual interactive entrypoint."""
import sys
import interactive_v20 as entry
fault=sys.argv.pop(1)
original=sys.stdout
class OutputFault:
    def __init__(self):self.used=False;self.pending=False
    def write(self,data):
        if not self.used and '"event": "independent_evaluation"' in data:
            self.used=True
            if fault=='write':raise BrokenPipeError('injected before evaluation write')
            if fault=='flush':self.pending=True
        return original.write(data)
    def flush(self):
        original.flush()
        if self.pending:
            self.pending=False
            raise BrokenPipeError('injected after evaluation bytes flushed')
if fault in ('write','flush'):sys.stdout=OutputFault()
elif fault=='scorer':
    def fail(*args):raise OSError('injected scorer exception')
    entry.suite.evaluate=fail
else:raise ValueError('unknown test fault')
entry.main()
