# Allocation-11 start-gate STOP — main advanced after freeze

**Terminal disposition:** `STOP_BEFORE_CANDIDATE_MAIN_ADVANCED`.

The sole owner-confirmed window was 2026-10-02 02:45–03:00 UTC. The start-gate observation at 02:46:10.4763361 UTC fetched current main `ddc3a7771f409889fbde87d7da01944cd1a08b0f`, while frozen `FREEZE.json` required `b0c1f12285fbbd2d4335999e727dc3211b55139d`. Because main no longer matched, the prospective candidate was not invoked. This allocation is terminal; no re-freeze or retry was made.

Other observed checks: the pinned image digest was cached with image ID `sha256:048a0de5d432205f9d92a9dfd36f4cab1cd82dfbd1042ce2c51bd94f7e45d32`; RTX 3080 reported 0 MiB / 0%; C: had 189,248,528,384 bytes free; WSLc `list --all` showed only previously exited containers; the fresh formal output path did not exist. No container, process, image or data was started, stopped, modified or deleted during this gate.

Counts remain candidate=0, CUDA=0, formal auditor=0, retries=0. No transfer-inclusive performance result or crossover conclusion is available. The A11 construction FAIL and subsequent PASS remain separately retained. Allocation 10's prior STOP remains unchanged.

Exact gate output is retained in `observed_start_gate.txt`. This record supplements, but does not alter, the preregistered freeze or construction checksum manifest.