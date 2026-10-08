Successor to #3924 after its retained `STOP_FAKE_EXECUTABLE_MOUNT_MISSING` and merged evidence PR #4476. Preserve every #3924 source, allocation, raw artifact, audit and STOP unchanged. The earlier matrix did not invoke the intended fake executable, so it did not test the scientific broker hypothesis.

## H / T / D / C / U

**H** — On current main, a fake child exit 0 is recorded as 0 but `--once` returns 1 because the broker uses `broker.get("returncode") or 1`. Nonzero codes should propagate exactly; timeout and unavailable executable outcomes should be typed and fail closed. `--once` should process no more than one eligible request.

**T** — Fresh allocation `issue3924-orbstac-broker-contract-v2-20260926-01`. Current main at intake: `a718da028d33c9608433789676ddd7204d8c5d14`. Source broker Git blob `f307daafdfd36d1ab4faf39bb36c36350e6e67e4` (SHA-256 `034b2e72a28fc3defb1b48195a2a8d3450e850895a4b3b7b7919dca44e198775`); existing test blob `e645ae575cd6fdae02556df9facc9919739584f3` (SHA-256 `a28b59232e55956a11bd87a35812b7d77df16febe5510c68fb80eda03a3ede1c`). OrbStack 29.4.0 linux/arm64, pinned cached `python:3.12-slim` image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. Formal runner performs an in-container preflight that verifies `/study/fake_codex.py` exists, executable, and hash-matched before any case. Mount the checkout read-only at `/repo`, this study read-only at `/study`, and a fresh dedicated output mount at `/evidence`. `--network none`, read-only root, bounded CPU/memory/swap/PIDs, drop all capabilities, no-new-privileges, bounded tmpfs. No host environment or credentials are forwarded. Exactly one formal container with seven cases: fake exit 0, fake exit 23, timeout, intentionally unavailable executable, malformed request, `--once` no-request with external 300 ms bound, and two queued requests. Then run the frozen raw-only audit once in a separate equivalent isolated container. No real model/provider/GUI/input/seed; no retries or post-result tuning.

**D** — `FAIL_ZERO_EXIT_PROPAGATION` if receipt records child 0 while the broker process exits nonzero. Exit 23 must propagate exactly; timeout/unavailable must be typed non-success; malformed input must fail closed; idle must emit no receipt and be externally bounded; two queued requests must create exactly one response/receipt/fake invocation for the sorted first ID. IDs and raw hashes must reconcile. `PASS_BROKER_EXIT_CONTRACT` requires all rows and independent audit with zero errors. Any source/image/mount/runtime/provenance/audit gate failure is STOP, not scientific PASS/FAIL; preserve output and do not rerun this allocation.

**C** — Fake executable only, no shared source modifications, no credentials, network, model/provider, GUI, user input or seed. Additive branch `research/issue-3924-broker-orbstac-v2-20260926`; additive path `research/integration/issue_3924_broker_exit_contract_v2/**`. Keep #3924 and PR #4476 unchanged.

**U** — One OrbStack Linux/arm64 broker contract only. No model utility, GUI/task correctness, efficiency, Docker Desktop equivalence or product claim.

## Execution roadmap

Freeze/read back source and gates → construction-only validation → one formal seven-case container → independent raw audit → additive evidence PR → merge/read-back on main only if review/checks pass.
