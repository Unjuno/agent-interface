# Same-client X11 window lifecycle — Issue #3950

**PASS_WINDOW_LIFECYCLE_BOUNDARY_SCOPED.** One formal invocation; no retries or post-freeze source changes. The result is a scoped identity boundary, not a production or task-success claim.

| Four sessions per comparison | Typed #881 | + server/process lifetime | + observed window lifecycle |
| --- | --- | --- | --- |
| Unchanged, later capture | match 4/4 | match 4/4 | match 4/4 |
| Same-content repaint | match 4/4 | match 4/4 | match 4/4 |
| Unmap/remap | match 4/4 | match 4/4 | match 4/4 |
| Old receipt after destroy/recreate | match 4/4 | match 4/4 | **mismatch 4/4** |
| Fresh replacement receipt, later capture | match 4/4 | match 4/4 | match 4/4 |
| Real observer connection restart | match 4/4 | match 4/4 | **UNKNOWN 4/4** |

**24 comparisons / 72 classifications / 28 actual pixel captures.** All four replacement cases retained the same live client/server process identities, XID, geometry and exact non-flat pixels. Actual DestroyNotify/CreateNotify and a server-observed BadWindow/child absence separated the lifetimes. All 16 same-incarnation positives matched; all four stale lifecycle receipts refused; all four new observer lifetimes remained UNKNOWN. All actors/Xvfb servers exited 0, private sockets disappeared and terminal windows/keys/buttons were empty.

Independent stdlib-only audit: zero errors, 12/12 evidence corruptions rejected. Construction unit tests: 12/12. Offline malformed/gap/authority/XID controls: 24/24 fail closed. No model call, XTEST or task-input operation occurred.

## H / T / D / C / U

**H:** Matching XID, process/server lifetime and current pixels cannot establish the same window incarnation. Event-derived lifecycle evidence can distinguish this controlled replacement without overinvalidating repaint/remap.

**T:** Four private Xvfb/actor pairs, one unchanged client connection per pair, deliberate reuse of that client's freed resource ID. Separate observer connection subscribes to root SubstructureNotify before creation and captures actual window bytes. The exact historical #881 classifier is used unchanged; this new candidate only adds observation-only refinements.

**D:** The pre-registered 24-comparison matrix and all failure/UNKNOWN/cleanup/source/audit gates passed. First formal outcome only. `SUMMARY.json` records counts and digests; the full protocol/report and exact sources are in the verified bundle.

**C:** Controlled synthetic client, not natural reuse frequency. Process ownership here is cooperative child identity plus independent /proc reads, **not authenticated XRes ownership** or an execution of the existing XRes guard. Root-only events do not prove coverage under reparenting or undetected delivery loss. A declared gap returns UNKNOWN. Event sequence numbers are not treated as global generation identifiers. All real receipts remain authority-free.

**U:** No production action admission, atomic check/use, model quality/cost, arbitrary toolkit, cross-platform, durable epoch or complete integration claim. Matching lifecycle evidence is still not input authority. Old #881/#902 evidence is preserved and the broad roadmap remains open.

## Environment and failure retention

Provided Linux6.18.44/x86_64/glibc2.41 execution container; Python3.13.5; Xvfb package `2:21.1.16-1.3+deb13u1`; Python-Xlib module `(0,15)` with no distribution metadata. Docker CLI/image identity unavailable: **no Docker/OrbStack equivalence or network-none container claim**. Xvfb explicitly used `-nolisten tcp`; this experiment made no network request or host-desktop/input action. Executable and 56 installed Xlib source digests are frozen.

Construction-01's missing-Xauthority STOP and failed runner are retained. Construction-02 used an experiment-private empty Xauthority file, redirected Xlib diagnostics to retained stderr and passed excluded construction. Formal sources/gates were then frozen on GitHub before the sole invocation. Repository-wide tests were not run; scoped audit/unit success is not full CI success. The separate auditor is an independent implementation/process, not an independent human review.

## Retrieve and independently audit

The four base64 parts encode one SHA256-bound tar.xz archive. Splitting is for byte-preserving GitHub MCP transport, not separate allocations. All source files, exact FREEZE.json, construction failure/success records, raw/partial formal observations, pixels, launcher receipt and auditor outputs are included. The visible `candidate.py` and `predecessor.py` are byte-identical to their frozen bundle copies.

```sh
python unpack.py /tmp/issue3950-evidence-new
cd /tmp/issue3950-evidence-new
python -B audit.py formal-same-client-window-lifecycle-20260922-01/raw.json --freeze FREEZE.json --out audit-recheck.json
python -B -m unittest -v test_candidate
```

Extraction verifies the archive and every manifest entry, refuses overwrites, and executes no study. The raw-only audit uses the standard library and imports no runner, candidate, predecessor or Xlib. The consumed `execute.py` must not be rerun; a new live replication needs its own issue/allocation, preflight and freeze. Read extracted `REPORT.md` for complete H/T/D/C/U, provenance and limitations.

## Provenance and integration

- Source main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
- Allocation: `same-client-window-lifecycle-20260922-01`.
- FREEZE.json: `fc6f1fa44d6b104644bf5e7f890923984d5b0d75e81d6e140e880ac8b99d01d6`.
- Formal raw: `13a77fff8a61e3377741c1e45eab374e939b8d0edb5ff97c4c9fdd39d8b6cdab` (223,980 bytes).
- AUDIT.json: `99ba499f9dbc150ea79c5eae9723ada5350d4f5f8d810263d091e5899e7b0cee`.
- Bundle tar.xz: `1b7d62ae6549b77d7cbcc672ba94728dfb7b09bf6331670e534635d378a597c5`.

[Issue #3950](https://github.com/Unjuno/agent-interface/issues/3950) contains the hypothesis, pre-formal hash record, construction digest clarification and formal result. The exact predecessor is Git blob `91983ab78a06b93cc7fdd829b6094fd255f18210` from [closed #881](https://github.com/Unjuno/agent-interface/issues/881). [#902](https://github.com/Unjuno/agent-interface/issues/902) explicitly excluded within-client resource reuse; [#3553](https://github.com/Unjuno/agent-interface/issues/3553)/[#3575](https://github.com/Unjuno/agent-interface/issues/3575) concern a different process-replacement/ownership boundary. [X11 protocol](https://xorg.freedesktop.org/archive/X11R7.7/doc/xproto/x11protocol.html) is the public event/resource reference, not the source of these measurements.

Integrate as **research evidence only**. Do not promote this root-only tracker into shared runtime. The next live boundary is whether the actual observer covers reparenting, gaps and reconnects and transports window generation into recovery, while preserving UNKNOWN whenever coverage cannot be established.
