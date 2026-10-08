# Retained predicate-retry evidence rescue

Latest main merged cleanly at 14ceb784b. Fresh normal/-O verification again
checks99 targets and reproduces the committed saved reports byte-for-byte.
Local CI43 again exits0 failures=[]; full transcript is merged-local-ci.log.

Source: a0e0d8da7c920ed0bc0079bedf5f9d7b7c7d8ecb,
research/17-predicate-retry-deadline-b64b. Original packet is preserved
byte-for-byte in research/concurrency/predicate_retry_deadline_17_20261003_b64b.

Fresh saved-only verification checks 99 manifest targets, then runs the original
independent oracle on retained MODEL and nine construction cells. Normal Python
3.14.5 and optimized Python both reproduce every original audit field. Source
programs are copied into a temporary directory and parsed, never executed.
No container/model producer or consumed historical allocation was replayed.

The finite outside-Condition policy admits an expired retry cycle (16 states,
28 edges); baseline has 4/4 and private deadline-first 17/24. These finite
characterizations are not latency, probability, strong fairness or hard-total-
deadline guarantees. Deadline-first loses a fresh-match priority case and is
NOT adopted into current production. Original V1 clock-order STOP, parser error,
publication errors and all raw records remain unchanged.

The first fresh wrapper attempt failed solely because its repository-root
parent index was 4 instead of 3; corrected before the successful runs. This is
not a historical experiment failure or a product regression.

Run: python3 runtime/results/predicate_retry_rescue_a0e0/verify_saved.py
Repeat with -O. Frozen local CI passed 43 steps with no failures at
5b14aa3b3; full output is local-ci.log. This is the exercised local CI gate,
not whole-repository/native certification or a new formal container run.
