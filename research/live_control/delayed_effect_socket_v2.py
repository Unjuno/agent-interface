"""Run the fetch-based delayed-effect fixture behind the durable socket."""
from pathlib import Path
import sys
import stopped_socket_v2 as bridge
from checkpoint_cause_cursor_v1 import EventCursor
from command_once_v3 import CommandOnce

bridge.EventCursor = EventCursor
bridge.CommandOnce = CommandOnce
HERE = Path(__file__).resolve().parent
if sys.argv.pop(1) != 'chromium':
    raise SystemExit('domain must be chromium')
original = bridge.subprocess.Popen


def spawn(args, **kwargs):
    args = list(args)
    index = next(i for i, value in enumerate(args) if str(value).endswith('interactive_v27.py'))
    args[index] = str(HERE / 'delayed_effect_browser_entry_v2.py')
    return original(args, **kwargs)


bridge.subprocess.Popen = spawn
bridge.main()

