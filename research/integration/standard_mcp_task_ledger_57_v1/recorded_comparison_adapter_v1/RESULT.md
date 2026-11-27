# Recorded caller to matched comparison adapter — 2026-11-21

## Question

Can the existing durable provider/MCP recorder journal be projected into one
measured-run input and accepted as a three-arm matched block without inventing
missing lifecycle, raw custody, or effect-attribution evidence?

## Result

**PASS_CONTRACT_SCOPED.** The new research adapter accepts a complete recorder
receipt, frozen comparison pins, contiguous full-lifecycle phases, image and
observation joins, and an explicit effect-attribution envelope. It verifies
each referenced file under the recorder root against SHA-256, requires every
journal event's raw refs to appear in the top-level receipt, and passes the
projected record through the existing measured-run validator. Three synthetic
recorded runs form a valid A/B/C matched block. Missing effect attribution,
an incomplete receipt, and a mismatched raw digest fail closed.

Normal and optimized Python runs each pass 6/6 adapter tests. The combined
R149/R281 attribution, matched-measurement, and adapter suite passes 33/33 in
both modes. The latest post-hardening matched summary and complete per-arm
records are under `raw-r03/`; earlier synthetic captures remain under `raw/`
and `raw-r02/`. The recorder request/response, event journal, score state and
synthetic delivered image files are hash referenced. `SHA256SUMS` covers
conditions, adapter and fixture source hashes, runner, all three raw runs,
measured records, summaries, and all normal/optimized logs.

After PR #10373 merged as `428a38eaac2dce07c7b7557985ec58a998d8736b`, the
combined 33-test suite was rerun against that exact main tree and again passed
33/33 normally and 33/33 under `-O`. The post-merge logs are retained beside
the original candidate logs. GitHub's `replay-gate` and `public-navigation`
checks passed; `formal` was skipped. No required branch protection was
configured at merge time.

The final manifest includes both post-merge logs and all three synthetic raw
generations; all 86 listed entries verify against disk.

## Limits

This is a deterministic offline contract fixture, not a live provider, GUI,
WSLc, Docker, MAP01, Mindustry, or efficiency experiment. Comparison pins,
phase boundaries, image delivery, independent scorer identity, and expiry /
release / horizon / effect times are supplied by the fixture caller. The
adapter cannot prove their truth or bind an owner receipt to a provider action
identity. Provider-internal retries remain unobservable unless independently
reconciled. Do not count these synthetic scores or token counts toward Issue
#57's empirical comparison.

The next integration work is to add a production-bound caller receipt carrying
identity-linked native owner expiry, confirmed release and neutral-horizon
evidence, then reconcile every model attempt against independent provider
receipts. Any missing field must remain unknown and block eligible success or
correctness-qualified break-even. Issue #57 remains open.
