# Issue #3876 — live producer to passive-reader integration probe

## H / T / D / C / U

- **H:** The already-existing `interactive_v17` producer's own prepared delivery stream can be consumed during a live producer process by the merged `event_inbox_reader_v1` CLI, then resumed from a caller-saved cursor after the producer appends terminal records, without changing event content/order or granting authority.
- **T:** One fresh Calc fixture through `interactive_v17` in a pinned local Docker image. Send only `clock` and `finish` protocol commands; read ready/initial observation/clock records while the producer is still alive, then resume the reader after finish and once more at the final cursor. No task edits, model, network, or OS input action.
- **D:** PASS only if the producer's exact stdout, `delivered.jsonl`, flush receipts, and concatenated reader responses reconcile byte-for-byte and by delivery ID/order; first read occurs while the producer is alive; the terminal append is recovered once from the saved cursor; the final read is empty; input-owner evidence shows no held keys/buttons; every reader response says authority none, acknowledged false, input_dispatched false; and an independent raw-only audit passes.
- **C:** Current main commit `cc9c500a339406c7de71df04c1d4b23f12fdbb09`; Docker Desktop linux/amd64; cached Calc/Xvfb base image `sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3`; pinned Python dependencies; formal container `--network none`, read-only root/source, bounded tmpfs, evidence-only writable mount. Additive branch/path; no production runtime changes.
- **U:** One synthetic Calc session and one existing producer lifecycle only. This does not demonstrate model receipt/viewing, ACK/consumption, producer restart identity, durability, multi-producer ordering, automatic wakeup, task success, latency benefit, or production promotion.

This is a distinct live-producer integration rung after PR #3883's component tests. It does not repeat the historical 15-record transfer or its synthetic writer/reader construction cases. The producer is the repository's existing `interactive_v17`; the consumer is the already-merged explicit reader CLI.

## Run protocol

`FREEZE.json` binds the exact base commit, experiment scripts, producer/source closure, reader source, pinned Python dependency set, and image config ID before the one formal invocation. The container runner starts a new producer output directory. It waits for `ready` and initial `observation`, sends a read-only `clock` command, and invokes the reader while the producer is still blocked on stdin. It persists the returned cursor separately, sends `finish`, reads the terminal records from that cursor, and performs one final empty read. Raw stdout/stderr, producer files, reader response bytes/cursors, process status, and hashes are retained.

The independent auditor reads retained files only; it does not import the producer, reader, or runner. Run it in a separate local Docker invocation with the repo and formal evidence read-only and an isolated audit-output mount.

## Reproduction

From a complete checkout at the frozen base commit, build the local image from the cached base and exact dependency pins. Record its config ID, then create `FREEZE.json` with `freeze.py`. Run the existing reader unit suite in Docker before freezing. The formal image ID is passed as an argument and checked against the freeze; mount only the checkout read-only and a fresh evidence parent read/write. Invoke `runner.py` exactly once at `results/live-reader-20260921-01/formal-01`. Run `audit.py` in a second `--network none` container with checkout and formal evidence mounted read-only and only a fresh audit directory writable. Never rerun into a populated output directory.

The runner accepts `--stream-id` only for construction checks; omit it for formal so the frozen stream identity is used. The final `audit.json` is a separate, independently produced artifact and does not rewrite the runner's raw evidence.

Do not rerun the formal allocation or overwrite its output path. Any STOP, mismatch, or audit defect requires a separately identified successor.
