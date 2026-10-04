# Result

The exact PR #7378 parent source (`fbed929f629dabaa9ae752019d0ee7151d4d2298`)
fails the cleanup-overlap regression when driven through `Backend.execute`, its
inherited executor method, and `Backend.raw`: the deterministic fake owner
records verified cleanup inside the explicit `up` bracket but emits no explicit
key-release command. The baseline leaves `ordinary_release_candidate=true`; the
candidate demotes it and refuses owner-transition verification. A cleanup
timestamp outside the bracket preserves the positive ordinary-release result;
missing cleanup records fail closed.

The current host-side execution-path suite passes 21/21, and the current host
owner-transition wrapper suite passes 8/8. An earlier WSLc run of the lower
`Backend.raw` boundary passed 21/21 and is retained with its original source
hash and swap/cgroup warning. The prior combined 29/29 run and first string-only
audit are preserved as historical receipts; the inherited suite includes
synthetic base-class cases, so those totals do not mean every case is reachable
through admitted v39 programs. The corrected host-side auditor parses one
terminal summary and retained exit receipts for each run, passes 12/12
retained-log checks with exit 0, and has five passing mutation tests.

This establishes a deterministic telemetry-classification boundary in the
adapter. It does not establish owner-thread queue scheduling, live input or
physical release timing, task effect, product reliability, or any model/GPU
claim. No live allocation was invoked or retried.
