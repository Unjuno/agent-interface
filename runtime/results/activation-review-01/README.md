# Caller-requested activation with review: candidate, personal use HOLD

Source `256614b9a81c7727dab64a76edd37daad5836732` adds optional public MCP
`review_after_activation=true`, default false. It composes existing activation
and review only after completed activation and verified neutral release. The
activation result remains separate from review. Review failure never retries
activation or claims no prior effect; an exception blocks editing. No grounding
or editing is performed by this composition.

Four new unit tests cover exact image retention/result lookup, failed or
unverified activation, failed review, and review exceptions. Initial tests
rejected the unknown option. An additional exception test failed with
`runtime_failed` before the receipt-preservation fix. These initial RED outputs
were observed in the conversation; they are not represented as archived logs.
Final retained native run 02 passes 345 protocol and 156 harness tests. Run 01
is retained but overlapped a subsequent edit, so it is not final-source evidence.

The first frozen personal X11 trial stopped after one observation. The caller
passed the whole response to the host's review function instead of its explicit
attempt number. The host marked evidence incomplete and rejected further
requests, including public close. Direct transport close exited 0; all owned
fixture processes terminated, with exact exit values retained. No mint, activation
or task input was dispatched. Independent fixture effects are empty for A and B.
This is a retained caller failure, not successful feature use or task completion.

The archive includes all trial files, original host logs, exact build/plan,
executable source and both native runs. The raw-only verifier checks hashes,
frozen files, the sole public request, missing review record, terminal exits and
no task effects under normal or optimized Python:

```sh
python3 runtime/results/activation-review-01/verify.py
python3 -O runtime/results/activation-review-01/verify.py
```

No primary task roundtrip reduction, speed, semantic latency, human tempo or
provider token/cost claim is supported. Candidate adoption remains HOLD until
a separately fixed caller and fresh case actually exercise this path.
