# Issue #4448 — resident XTerm construction pilot

Allocation `issue4448-construction-pilot-04` tests the core fixture mechanics for
the Issue #4448 ephemeral-vs-resident XTerm idea. It is a single construction
pair, not the preregistered 12-pair/96-action formal allocation.

## H / T / D / C / U

**H — hypothesis.** Reusing one XTerm and one child across four equivalent
Return actions can preserve exact fixture effects and neutral input state while
avoiding a per-action native XTerm teardown wait.

**T — treatment.** One ephemeral and one resident arm ran sequentially on one
private Xvfb/Openbox display. Each arm received four XTEST Return press/release
actions and used the same Python child effect writer. The ephemeral arm launched
one XTerm/child per action and waited for each XTerm exit. The resident arm kept
one XTerm/child through all four actions, then measured its final shutdown.
Each action's effect was an append-only JSON receipt; the parent observed the
receipt and independently polled XQueryKeymap until all keys were up.

**D — construction decision.** `PASS_CONSTRUCTION_MECHANICS_ONLY`: both arms
produced 4/4 effect receipts, 4/4 neutral-key observations and zero child/XTerm
nonzero exits. Ephemeral XTerm PIDs were four distinct values and each child
PID was distinct. Resident reused one XTerm PID and one child PID for all four
receipts; the XTerm remained live after each effect and exited 0 on final
shutdown. The stdlib-only independent auditor reports `errors=[]` and rejects
5/5 copied-result corruption controls. No performance decision is made from a
single pair.

Observed pilot values (descriptive only):

| Arm | Session wall | Effect → next-ready median | Maximum |
|---|---:|---:|---:|
| Ephemeral | 351.908 ms | 9.075 ms | 10.533 ms |
| Resident | 94.112 ms (includes final shutdown) | 0.094 ms | 0.128 ms |

The Issue's formal criteria remain unchanged: 12 matched pairs/96 actions,
paired latency distribution gates, at least 10/12 lower full-session resident
wall times, process/effect/release reconciliation, and independent raw audit.

**C — controls.** No model, provider, network, GUI outside private Xvfb, user
desktop/data, or shared runtime code was used. The source directory and container
root were read-only; `/tmp` was a bounded 64 MiB tmpfs; only the output mount was
writable. Docker network was disabled. The cached image's Xvfb startup contract
also loads its packaged X11 font path before Openbox/XTerm start.

**U — limits and stops.** The requested Issue environment is Linux x86_64 with
CPython 3.13.5. The available cached OrbStack image is Linux/arm64 with CPython
3.12.14. Therefore this pilot does not meet the Issue's formal environment and
cannot establish the registered latency criteria or an x86_64 result. Formal
allocation was not frozen, assigned a seed, or invoked. Preserve pilot-01
(read-only font-cache setup stop), pilot-02 (same child-ready stop), and pilot-03
(diagnostic child absent at timeout) unchanged. Pilot-04 is the corrected
construction outcome after matching the cached image's Xvfb/font initialization.
No formal result is inferred from or pooled with those setup attempts.

## Reproduction

Cached image: `agent-interface-r3-batches:20260927-03`, image ID
`sha256:cb4e745a49e0ed05f6138d8608d9337028f30cd244c60f13063891782235f466`,
`linux/arm64`. The pilot runner SHA-256 is recorded alongside this report and
the raw files. Invocation:

```sh
RUN_OUT="$(mktemp -d)"
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --mount type=bind,src="$PWD/research/measurement/xterm_resident_teardown_4448_v1",dst=/src,readonly \
  --mount type=bind,src="$RUN_OUT",dst=/out \
  --entrypoint python3 agent-interface-r3-batches:20260927-03 \
  /src/pilot.py --allocation issue4448-construction-pilot-04 --output /out/run01
```

The host must create `RUN_OUT` as an empty directory before invocation; the
formal corpus/seed is not part of this pilot command.

Runner: `pilot.py`. Independent audit: `audit_pilot.py`. Raw output:
`pilot-04/run01/result.json`; independent audit: `pilot-04/audit.json`.
Runner SHA-256: `a312d33bce69cbb51cc1bcf72083f5603f56b98db19860c0c9584619f75397a3`.
Auditor SHA-256: `3961ede36940d4a9240abb0564deb82738de8fa86d4be1369bbd03d7968ebf8e`.
Raw result SHA-256: `e4e9635e47cab7b05b373787cfd177f14a150d784f400d65c5b95f2847ca7b89`.
Audit SHA-256: `3fa41b8e8605b703f98c0ce1a3a584f83b2ebbed262f8cdd5a6eadf11ee60d73`.
The same independent audit run in the cached container reproduced the host audit
byte-for-byte. Setup stops are preserved in `pilot-01`, `pilot-02`, and `pilot-03`.
