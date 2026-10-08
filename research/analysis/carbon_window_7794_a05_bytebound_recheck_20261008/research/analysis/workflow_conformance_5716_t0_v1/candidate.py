import json,sys
def classify(projection):
    if projection["completeness"].get("release") is not True:
        return "UNKNOWN_TELEMETRY"
    release_events = [event for event in projection["events"] if event.get("kind") == "release"]
    return "CONFIRMED_COMPLETE" if release_events else "CONFIRMED_OMISSION"

inputs = json.load(sys.stdin)
for projection in inputs:
    row = {"projection": projection, "classification": classify(projection)}
    print(json.dumps(row, sort_keys=True, separators=(",", ":")))
