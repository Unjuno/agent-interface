from __future__ import annotations
import json
import os
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "parents" / "scorer_feedback_attribution_59_t0_a04_20261004"))
sys.path.insert(0, str(ROOT / "parents" / "main"))
from scorer_feedback_attribution_v3 import attribute_positive_events as a04
from scorer_feedback_attribution_v4 import attribute_positive_events as a05
from independent_progress_clock_v2 import ProgressClock, ProgressSample

SAMPLES = [{"schema":"independent-progress-sample-v2","sample_ns":100},
           {"schema":"independent-progress-sample-v2","sample_ns":200}]
INTERVALS = [{"intent_token":"intent-a","key":"ATTACK","admitted_ns":90,
              "release_sync_ns":210,"release_verified":True}]

def run():
    rows=[]
    cases=[
        ("KILL_COUNT_INCREASE", "positive", True),
        ("MAP_EXIT", "positive", True),
        ("FUTURE_SCORER_EVENT_V3", "positive", True),
        ("KILL_COUNT_INCREASEE", "positive", True),
        ("PLAYER_DEAD", "negative", False),
    ]
    for sequence,(kind,polarity,useful) in enumerate(cases,1):
        event={"schema":"independent-progress-event-v2","event_sequence":sequence,
               "observed_ns":200,"kind":kind,"polarity":polarity,"useful":useful,
               "controller_visible":False}
        case={"case":f"{sequence:02d}-{kind}","event":event}
        case["a04"]={"accepted":True,"rows":a04(SAMPLES,[event],INTERVALS)}
        try:
            case["a05"]={"accepted":True,"rows":a05(SAMPLES,[event],INTERVALS)}
        except ValueError as error:
            case["a05"]={"accepted":False,"error":str(error)}
        rows.append(case)
    result={"schema":"scorer-feedback-attribution-a05-raw-v1",
            "producer_vocab":["KILL_COUNT_INCREASE","MAP_EXIT"],
            "producer_negative_vocab":["DEATH_COUNT_INCREASE","PLAYER_DEAD","EPISODE_FINISHED_NO_EXIT"],
            "cases":rows,"formal_live_allocation":False,
            "scope":"synthetic schema-construction; no task/game/model/input"}
    out=Path(os.environ.get("A05_OUT", str(ROOT/"out"/"candidate.raw.json")))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__ == "__main__": run()
