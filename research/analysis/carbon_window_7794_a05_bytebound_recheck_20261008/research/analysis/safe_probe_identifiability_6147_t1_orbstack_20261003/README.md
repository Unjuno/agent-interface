# Issue #6147 T1: disposable X11 GUI transfer

This is a fresh GUI-boundary experiment, distinct from #6147's consumed T0 A01–A05 outcomes. The T0 A03 FAIL_AUDIT_CONTROL_COVERAGE and A04/A05 analytical results remain unchanged. This fixture tests the post-probe qualifications in actual rendered X11 pixels and terminal effect receipts; it does not exercise any real app or runtime.

## Frozen question

Can the pixel-only adaptive policy safely act at the current state after probing when:
- an aliased A/B initial pair separates to LEFT/RIGHT and the corresponding current terminal action is safe;
- C/D remain distinct but action-equivalent for COMMON;
- E/F remain indistinguishable under safe P/Q and must yield;
- G/H become visibly target-expired after P→Q and must yield despite distinct outputs; and
- I/J converge under P→Q to shared action-equivalent terminal Z, where COMMON is safe without claiming their initial identities?

See PROTOCOL.md for H/T/D/C/U, exact arm outcomes, stop rules, and scope. The pre-run identity and invocation vectors are in FREEZE.json; SHA256SUMS.txt binds the frozen source and inputs. Historical construction-only attempts, including runner stops, are retained under construction_smoke/.

## Isolation

Each arm runs a fresh hidden-state fixture/Xvfb container and one candidate container sequentially. A separate auditor container receives only retained candidate and fixture raw logs. Candidate gets only candidate.py, policy.py, model.json, public context, and a read-only X11 socket. The hidden deck, fixture source and oracle log are not mounted into the candidate. No network, model, GPU, game, user data, host UI, or external effect is used.

Pinned image: issue4466-gtk-pixel-stability@sha256:7c202113e519666007d7f6a74fa4a9854ed7cec62c07c1e80631474e69af7a27 (linux/arm64); OrbStack Docker Engine 29.4.0 (linux/aarch64). Each formal container requests 1 CPU, 512 MiB memory, 64 PIDs, network none, read-only root, bounded /tmp, all capabilities dropped, and no-new-privileges. Swap is not disabled: construction cgroups reported memory.swap.max=536870912; Docker inspect reported MemorySwap=1073741824.

## Exact execution

From the repository root, after checking exact latest main, Issue/PR/branch ownership, fresh raw/formal_01/ output path, image digest, and current OrbStack inventory:

    sh research/analysis/safe_probe_identifiability_6147_t1_orbstack_20261003/run_formal.sh

The runner refuses a pre-existing formal output directory and exact container names. It runs adaptive, no_probe, and one_step once each (one candidate per arm); only after all three arms complete does it run the separate raw-only auditor once. It preserves stdout, stderr, exit codes, inspect data, oracle JSONL, Xvfb log, and auditor JSON. The runner is no-retry; a failed formal invocation is retained as STOP/NOT_EVALUATED, not repeated.

## Integration handoff

The first formal allocation stopped on an Xlib teardown race before completing all arms; see [STOP.md](STOP.md), [REPORT.md](REPORT.md), and [RUN_RECORD.json](RUN_RECORD.json). The partial raw is immutable and has its own [SHA256SUMS.txt](raw/formal_01/SHA256SUMS.txt). It is not a semantic result, and the remaining arms/auditor were not invoked. Any future attempt must be a separately frozen successor allocation and must not alter this evidence. Do not close #6147: real-app transfer and broad applicability remain open.
