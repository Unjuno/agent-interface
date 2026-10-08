# Result — auxiliary Codex event accounting

Status: **PASS — narrow plain/no-image schema preflight only.** This is not six-task, GUI, task-effect, or semantic-quality evidence.

## Experimental result

- OrbStack context: `orbstack`; Linux/aarch64 host reported by daemon.
- Container: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--network none`; read-only root; source/data mounts read-only; temporary `/tmp` where needed.
- Backend source pinned to PR #3647 head `6a942ea04bfea1d196d19719ec59a9bdad720826`; model `gpt-5.6-luna`, low reasoning effort.
- Eight isolated event-accounting controls passed in OrbStack, including replay of the exact prior warning+assistant stream and six fail-closed mutations. The first run without a writable tmp directory failed all eight tests during temporary-directory setup; rerun with `--tmpfs /tmp` passed 8/8. This environment setup failure is retained in the preregistration.
- Exactly one fresh host model call was made. IPC request id: `c24a2ae263da492ca7b1fc3bdcb73322`; mode `handle`, image null, authority false. Broker and CLI returned code 0; no retry.
- Stream contained one known warning item (SHA-256 `ab4a4e7e16182afebbe24848add270e2d0b577e30d12ef830503e1f5d13c4a7f`), one assistant message, and one completed turn with usage: 12,302 input; 99 output; 35 reasoning output; zero cached/cache-write input tokens.
- Candidate receipt: `PASS`, assistant count 1, warning explicitly classified. Independent offline Draft 2020-12 schema audit: `PASS`, one message, one turn, schema-valid JSON object. Raw stream SHA-256: `6262ec35844921b0807ef84443ffffaaaadc0b9643de4e4cfcd1095bec2cd682`.
- Broker stderr contains local CLI cache/state warnings and unauthenticated optional Cloudflare MCP shutdown warnings. The host Codex CLI nevertheless returned a structured completed stream and exit code 0; this does not alter the protocol gate.

## Scope and disposition

The successor runner handles the observed auxiliary event shape without weakening rejection of unknown event types. This result verifies only one plain/no-image schema preflight on the selected backend. Compiled schema and six-task integration remain untested; Issue #2849 stays open.

## Reproduction

Run the copied test suite in `evidence/offline` with OrbStack, network disabled, read-only root, and `--tmpfs /tmp`:

```sh
docker --context orbstack run --rm --network none --read-only \
  --tmpfs /tmp --mount type=bind,src="$PWD/evidence/offline",dst=/test,readonly \
  --workdir /test python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python -m unittest -v test_event_accounting
```

Raw fresh-call request, response, broker, candidate receipt and independent audit are in `evidence/fresh-plain/`. The previous failed runner's event stream is separately retained in `evidence/offline/previous-failed-events.jsonl`; the historical bundle in main is unchanged.
