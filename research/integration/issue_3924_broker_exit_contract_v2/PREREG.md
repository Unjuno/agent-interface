# Preregistration — Issue #4485

Allocation: `issue3924-orbstac-broker-contract-v2-20260926-01`.

## H / T / D / C / U

**H** — The broker's `--once` path records a fake child exit 0 but returns 1 due to `returncode or 1`; it should propagate 0 and other child exits exactly. Timeout and unavailable executable outcomes should be typed non-successes. One-shot mode should process at most one eligible request.

**T** — Current main at freeze: `21dd6a26dbd9f5cb4a6e11b1060902799a76a733`. Broker Git blob `f307daafdfd36d1ab4faf39bb36c36350e6e67e4`, SHA-256 `034b2e72a28fc3defb1b48195a2a8d3450e850895a4b3b7b7919dca44e198775`; test Git blob `e645ae575cd6fdae02556df9facc9919739584f3`, SHA-256 `a28b59232e55956a11bd87a35812b7d77df16febe5510c68fb80eda03a3ede1c`. OrbStack 29.4.0 linux/arm64; pinned image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a`. Frozen fake executable SHA-256: `c9855dcc434b3bd52c9d1a5d35d0fadb72f338d2e7fefde11499f91ed849c64a`. Frozen formal runner SHA-256: `e63bff05625f885201971b05830dd90316b82e1b62ca7e4d357b65ea116fef86`. Run one outer formal container after in-container preflight verifies fake executable path and digest. Seven cases: child exit 0, exit 23, timeout, unavailable executable, malformed request, idle `--once` bounded externally to 300 ms, and two queued requests. Then run the raw-only audit once in a separate isolated container.

**D** — `FAIL_ZERO_EXIT_PROPAGATION` if receipt has child 0 but broker exits nonzero. Exit 23 must propagate exactly; timeout/unavailable typed non-success; malformed input fails closed; idle emits no receipt and is externally bounded; queued requests produce exactly one receipt/response/invocation for the lexically first ID. Require raw hashes and independent audit with zero errors for `PASS_BROKER_EXIT_CONTRACT`. Any provenance, mount, image, runtime, or audit gate failure is STOP, never scientific FAIL/PASS.

**C** — Fake executable only. No real model/provider, credentials, network, GUI, user input, seed, or source modifications. Checkout read-only at `/repo`, this directory read-only at `/study`, dedicated output at `/evidence`; network disabled, read-only root, bounded resources, all capabilities dropped, no-new-privileges.

**U** — One OrbStack Linux/arm64 contract only; no model utility, GUI/task correctness, efficiency, Docker Desktop equivalence, or product claim.

## No-retry rule

The formal allocation is single-use. Preserve any infrastructure/audit failure and do not rerun, tune, or relabel it. Construction checks are not formal rows.
