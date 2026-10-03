# First native result — scoped support, not deployment certification

Issue #5531 N01 candidate once exit 0 and raw-only auditor once exit 0. First immutable scientific status: SUPPORTED_NATIVE_LIVENESS_BOUNDARY_SCOPED. Raw SHA256 89672077965d4caee4d62e4209768a30eb717f10ef56105460cc418497bca2c6; prospective freeze b42dc372c074b8c2ee18648c3cf6d595dfa41c2d53c31dec7953770161c5fa4a. No formal repair, retry or regrade.

Three repeats of four fresh private Xvfb fixture cohorts (12 total):

|Cohort|Checkpoint evidence|Final read evidence|Typed classification|
|---|---|---|---|
|healthy_fast ×3|Result already available; normal worker exit 0|Native read finish GO+0.081–0.144ms|RESPONSIVE_SCOPED|
|healthy_server_blocked ×3|No result, owned worker not terminal|Same PID/start-ticks/nonce valid read finish GO+100.743–106.294ms|SUSPECTED_UNAVAILABLE → RESPONSIVE_SCOPED|
|killed_server_blocked ×3|Owned SIGKILL; waitpid exit -9, no result|No reply; terminal retained|FAILED → FAILED|
|invalid_response ×3|Genuine native read, planted incorrect emitted focus|Native focus matches oracle but corrupted wire field is invalid|EVIDENCE_INVALID → EVIDENCE_INVALID|

Actual scheduled 30ms observation checkpoints were GO+31.127–40.127ms; they are not exact deadlines. All fast/invalid native reads finished before nominal GO+30ms, and all healthy blocked workers remained alive without replies at their later actual checkpoint. The nominal kill+10ms operation was observed at GO+10.861–14.842ms. No hard latency guarantee or simulation-only transfer claim. No assertion that crash and delayed full transcripts match: crash EOF and OS terminal evidence distinguish them.

The timeout-as-crash baseline labels the three delayed healthy workers FAILED at the checkpoint, contradicted by their alive owned-child status and later valid native reads. Typed policy reports suspicion instead and makes zero false crash labels in those three cells. A completed healthy worker's reply is historical scoped responsiveness, not proof it remains running after completion. Normal exit 0 is not the induced-crash failure class. A planted semantic invalidity does not authorize valid-response clear. Terminal absorbing and stale-generation refusal are additionally covered by unit/schema-copy tests, not claimed as extra native crash/restart cohorts.

Auditor imports neither candidate policy nor Xlib, reconstructs its saved predicates and rejects 8 explicitly modified copies (authority, boolean-for-integer emission/PID, stale nonce, cleanup violation, wrong final classification, healthy terminal violation, killed exit violation). This is independent code-path audit under owned instrumentation assumptions, not a separate external observer or malicious-forgery-resistant verifier. It does not authenticate arbitrary trace writers. All fixture queries are genuine Xlib GetInputFocus; invalid-response corruption is explicit test injection after a genuine read.

Keymap empty, observed Button1–3 neutral, owned controller closed, all private Xvfb exits 0, expected worker terminal statuses, zero input emissions/dispatch authority in all 12 cells. Container cgroups: cpu.max 100000 100000, memory.max 536870912, memory.swap.max 0, pids.max 128. Read-only source/root, network none, pinned cached image, bounded /tmp, own output only. VM is shared-host normal OrbStack (not security-isolated or exclusive CPU); other workers/resources untouched. Own Engine zero running containers after stages, VM stopped; receipts retained.

Construction: initial policy stub six failed tests (RED), implemented policy six GREEN; final host/container suite 12 tests. Excluded native preflight two rows; construction outputs preserved. LOCAL_CI.json records host package 12/12, workspace 22/22, scorer replay 2/2, namespace inventory 157/157, and frozen saved evidence checks. FILES.json hashes all final artifacts except itself. No production runtime, shared roadmap/index, predecessor experiment or old first status changed.

H/T/D/C/U are in PLAN.json. The old #5531 principle was already supported synthetically; this adds one native bounded-read transfer check, not a novel mechanism or optimum-budget claim. Still unverified: production scheduler/transport/loss, failure-domain independence, arbitrary writers, GUI/helper restart eligibility, input admission/ownership, recovery task effects, model utility, full CURRENT_GOAL/ROADMAP. Main integration should preserve this limitation and leave broad #5531 open.
