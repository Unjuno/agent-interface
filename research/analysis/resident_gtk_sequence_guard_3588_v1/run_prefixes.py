from __future__ import annotations

import json
from pathlib import Path

from oracle import snapshot
from policies_guarded import Resident as Guarded, last_message as guarded_last_message, message_count as guarded_message_count
from policies_original import Resident as Original
from policies_original import last_message as original_last_message, message_count as original_message_count
from traces import COMPARATORS, TRACES


def capture(klass, events):
    policy = klass()
    previous_actions = 0
    rows = []
    for index, event in enumerate(events):
        policy.step(dict(event))
        rows.append({
            "prefix": index + 1,
            "event": event,
            "state": snapshot(policy),
            "action_delta": [list(x) for x in policy.actions[previous_actions:]],
        })
        previous_actions = len(policy.actions)
    return rows


result = {
    "allocation_id": "issue3588-resident-gtk-sequence-guard-construction-01",
    "upstream_main_commit": "e1d9c073cdaed1a5eedf602f5959d83d39804f2b",
    "upstream_candidate_git_blob": "37bb7b271b099ccb10a594dbe00faa5bf618099b",
    "formal_gui_invocations": 0,
    "traces": {
        name: {"events": events, "original": capture(Original, events),
               "guarded_candidate": capture(Guarded, events)}
        for name, events in TRACES.items()
    },
    "comparators": {
        name: {"events": events,
               "original_last_message": original_last_message(events),
               "original_message_count": original_message_count(events),
               "guarded_last_message": guarded_last_message(events),
               "guarded_message_count": guarded_message_count(events)}
        for name, events in COMPARATORS.items()
    },
}
out = Path("/evidence/prefixes.json")
out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({"allocation_id": result["allocation_id"], "trace_count": len(TRACES),
                  "prefix_count": sum(len(v) for v in TRACES.values()),
                  "output": str(out)}, sort_keys=True))
