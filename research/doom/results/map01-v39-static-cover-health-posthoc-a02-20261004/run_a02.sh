set -eu
python3 -B /src/research/doom/results/map01-v39-static-cover-health-posthoc-a02-20261004/candidate.py /src/research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl > /tmp/candidate.json
cat /tmp/candidate.json
python3 -B /src/research/doom/results/map01-v39-static-cover-health-posthoc-a02-20261004/auditor.py /src/research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl /tmp/candidate.json
python3 -B -c 'import json; p=json.load(open("/tmp/candidate.json")); p["cover_samples"]["last"]["health"]=999; json.dump(p,open("/tmp/mutated.json","w"))'
if python3 -B /src/research/doom/results/map01-v39-static-cover-health-posthoc-a02-20261004/auditor.py /src/research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl /tmp/mutated.json; then
  echo NEGATIVE_CONTROL_UNEXPECTEDLY_PASSED
  exit 9
else
  echo NEGATIVE_CONTROL_REJECTED
fi