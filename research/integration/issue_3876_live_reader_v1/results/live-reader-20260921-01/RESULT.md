# Issue #3876 live-producer/passive-reader result

Disposition: `PASS_LIVE_PRODUCER_READ_SCOPED` — independent raw-only audit, 0 errors.

## H / T / D / C / U

- **H:** The existing `interactive_v17` producer's prepared delivery stream can be consumed while that producer is live, then resumed from a caller-saved cursor after it appends terminal records, without loss/reordering or authority transfer.
- **T:** One fresh LibreOffice Calc fixture, seed 387601, through `research/live_control/interactive_v17.py`; owner-assigned stream ID `interactive-v17-calc-387601-epoch-01`. The runner sent protocol-only `clock` and `finish`. It read the stream while the producer remained alive, explicitly persisted the cursor, resumed after finish, and made one final read.
- **D:** Producer exit 0; six delivered records in order: `ready`, initial `observation`, clock `command`, `clock`, finish `command`, `independent_evaluation`. Reader returned 4 while live, 2 from the saved cursor after terminal append, then 0. Producer stdout and `delivered.jsonl` are byte-identical (SHA-256 `46a495d982fa4fe1dc410a68dc1ae09e6a35ab6795421979c516c09f3f1ae384`); receipt order/count, logical event projection, image reference/presence, cursor prefix hashes and all three non-authority response flags independently reconcile. The actual application evaluation is `success=false` because no task was performed; this is not a task-success claim. Input owner reports verified empty release, no keys/buttons down.
- **C:** Main commit `cc9c500a339406c7de71df04c1d4b23f12fdbb09`; Docker Desktop 29.8.0 linux/amd64; final image config ID `sha256:cda81a9061bf72cad538ca0eca3094bad66d8afba21c6f69e0cd80e904c49d72`; base image config ID `sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3`; Python 3.12 and exact requirements are in `FREEZE.json`. Formal run: `--network none`, read-only root/source, bounded tmpfs, 2 CPUs/4 GiB/128 PIDs, evidence-only writable mount. Independent audit used a separate network-none container, read-only source/evidence and 1 CPU/1 GiB/64 PIDs.
- **U:** One local synthetic Calc session and one producer lifecycle. No model, task input, action replay, ACK/consumption proof, producer restart test, durable epoch persistence, multi-producer arbitration, automatic wakeup, useful-feedback/model-decision timing, performance, or production-promotion claim. The caller supplied the stream identity before producer startup; the producer itself still does not persist an epoch.

## Integrity and verification

- Formal allocation: `issue-3876-live-reader-20260921-01`; exactly one formal runner invocation.
- At PR preparation, fetched `main` at `fab3b392fb854696312a85a6b859a78369c3e737`. A direct Git comparison from frozen base `cc9c500a339406c7de71df04c1d4b23f12fdbb09` found no changes to any of the 40 frozen input paths, including the producer, reader and experiment sources; current-main source closure therefore still matches this run.
- Freeze: 40 source/input paths; retained at `formal-01/freeze.json`; SHA-256 `bf929d56e968884a403e74f78a6b9bec6d28e4c23594f0e19380619be300d7cb`.
- `runner_result.json` SHA-256: `b14c24e053c68e7c19861475430d3c1956fc8ac382686e7bca41313d0ff8e8ec`.
- Formal file-manifest SHA-256: `b36ba64b4b8ee274d035e8a48f23a90e89d3c1bd2821e547aee9112f3014fad4`.
- Independent audit: `audit-01/independent-01/audit.json`, SHA-256 `f413408e395b946cae465588898a7ca6cdf7c79ff25808ca53544582fc160e3f`; `PASS_LIVE_PRODUCER_READ_SCOPED`, `errors=[]`.
- Reader construction tests: 6/6 passed in local Docker before freeze; new experiment modules passed Python 3.12 syntax compilation.

All raw producer/reader stdout and stderr, event and delivery JSONL, image, owner-release receipt, saved cursors, process metadata, freeze and SHA-256 manifest are retained under `formal-01/`. Earlier construction stops and their untouched outputs are retained under `construction/` and described in `CONSTRUCTION.md`.

This result advances the live producer-to-reader boundary for #3876 only. The remaining owner-lifecycle/persisted-epoch, host presentation/model receipt, ACK/retention, restart, terminal-state and useful-feedback questions stay open; no production CLI/MCP path is enabled by this experiment.
