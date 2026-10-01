# Issue #6243 T0 successor-02 — formal result

## H / T / D / C / U

- **H:** With equal per-method times across arms, different method frequencies can alter natural-method whole-task ordering while descriptive common-method means remain equal; the exact equal-method null must remain equal.
- **T:** 12 constructed matched pairs / 24 attempt rows across four prespecified synthetic scenarios. One candidate invocation and one independent raw-only audit were run in the pinned CPU-only network-disabled Docker container.
- **D:** Scoped pass requires independent reconstruction of all rows, exact null, correct acquisition/horizon and unfinished-cost accounting, and rejection of four specified mutations.
- **C:** All observations, durations, method frequencies, acquisition cost, failure/switches, and unfinished penalties are constructed. The deterministic coders do not establish human coder reliability. Common-method contrasts are selection-conditioned and descriptive.
- **U:** No human/agent tempo, GUI/task effect, causal effect, population effect, product result, or external validity is inferred.

## Execution

Allocation: `METHOD-SELECTION-FAIRNESS-6243-T0-SUCCESSOR-02-20261002`; predecessor `method-selection-fairness-6243-t0-v1-20261002-01` remains unchanged as `FAIL_AUDIT_GATE`.

Runtime was OrbStack Docker, image `python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b` (`linux/arm64`), `--network none`, 1 CPU, 512 MiB RAM, 64 PIDs, read-only root and 64 MiB tmpfs. Candidate=1/1 exit 0; auditor=1/1 exit 0; retries=0. Exact command, runtime and raw receipts are in `formal-01/`.

## Result

The independent raw-only auditor returned **`METHOD_PASS_SCOPED`**: 24 attempts, four scenarios, no errors, and 4/4 mutation controls rejected. The constructed shortcut-mixture rows have equal method-conditioned times in both arms (ordinary 10,000 ms; shortcut 4,000 ms), while natural totals are H=22,000 ms and A=34,000 ms. With the constructed one-time H acquisition charge of 35,000 ms, H is slower at horizon 1 (57,000 vs 34,000 ms) but faster at horizons 4 (123,000 vs 136,000 ms) and 10 (255,000 vs 340,000 ms). The exact-null scenario is 72,000 ms in both arms. Switch/failure totals are H=24,000 and A=20,000 ms. Unfinished H attempts retain 16,000 observed ms plus 240,000 penalty (two 120,000 ms penalties), scored 256,000 ms.

These are programmed fixture values and demonstrate only that the frozen accounting pipeline detects the intended distinctions and controls. They are not empirical comparisons of methods. In particular this result does not resolve the human-tempo or agent-interface hypothesis in Issue #6243; an empirical successor needs independently coded real task traces and suitable allocation/consent.

## Reproduction and integrity

`formal-01/candidate_stdout.txt` and `formal-01/auditor_stdout.txt` preserve raw process output. JSON outputs are copied verbatim from the execution directory. `formal-01/SOURCE_SHA256SUMS` hashes frozen inputs; package `SHA256SUMS` covers every tracked package file except itself (not ignored local scratch outputs or bytecode caches). The host construction test and independent assertions over the retained formal audit output passed locally; the repository analysis-index workflow's focused tests are to be reported separately in the PR checks.

See [Issue #6243](https://github.com/Unjuno/agent-interface/issues/6243). This successor does not overwrite or reinterpret the predecessor failure.
