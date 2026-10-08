# Dated raw-only identity supplement — after the first formal result

Author postformal self-challenge found additional copied, rejoined evidence
accepted by frozen audit_v1: A05 signal.pid integer to same-valued float, display
to:999 and owner_ready.role to consumer. Actual raw retained integer signal PIDs,
six expected distinct displays and correct roles; the omission is in the auditor's
coverage. Original source/audit/10controls/native observations remain byte-identical.
The first local v2 test failed with ModuleNotFoundError before audit_v2 existed;
that test-first failure is retained in the session record, not a native failure.

Add audit_v2.py and seven tests. V2 rereads original raw, reruns v1 only in a fresh
temporary output and requires an identical original audit result, then checks
expected display, owner/consumer role and strictly positive integer signal PID
bound to that row's recorded owner process. Six targeted controls rejoin raw and
row.json: float/Boolean signal PID, foreign/aliased display and swapped owner/
consumer roles. It preserves each original v1 acceptance/refusal separately.
This is a supplemental engineering check, not retrospective preregistration,
retuned science, another native/formal allocation or a claim of complete audit
coverage. Original six-case conclusion and all physical cleanup evidence remain.

Reproduce on retained files, with a new output path:
`python3 -B audit_v2.py --cases cases.json --raw formal/01/run/raw.json --original-audit formal/01/audit/audit.json --output /tmp/clipboard36-identity-v2.json`.
Host stdlib tests: `python3 -B -m unittest test_audit test_audit_v2 -v`.
Original two line-framing tests were already executed in the pinned Linux image;
they need libX11 to import the frozen recorder and are not silently rerun here.
