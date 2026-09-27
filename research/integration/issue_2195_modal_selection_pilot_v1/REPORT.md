# Issue #2195 model-selection construction pilot

## Outcome

**`HOLD_PILOT_INFERENCE_TIMEOUT`.** The disposable Inkscape 1.4/Xvfb setup
successfully produced a real Save-As transient and a SHA-pinned screenshot.
The first host-local Ollama vision request exceeded its 240-second client
timeout and returned no model response. The frozen run stopped there: one
request started, zero responses, five rows not sent, zero retries. No
model-recommended input was executed. This is an inference-resource stop, not a
model-selection failure and not an Issue #2195 result.

## H/T/D/C/U disposition

- **H:** not evaluated; there was no response for the exact/fresh case.
- **T:** setup/capture portion completed in Docker Desktop; model phase stopped
  on the first local API timeout under the frozen one-shot protocol.
- **D:** HOLD, because no decision rows were returned. `RESULT.json` and the
  one-entry `responses.json` record the exact stop.
- **C:** one private Inkscape Save-As modal, one Qwen3.5 4B Q4_K_M model on CPU,
  six planned typed packets sharing one image, but only the first request was
  attempted. No held-out app, changed live modal, independent effect score,
  action dispatch, or end-to-end benefit was measured.
- **U:** local vision inference may be too slow for this host/timeout, but the
  single timeout does not establish general unavailability. Safe model choice,
  multi-modal transfer, and the full #2195 acceptance remain unknown.

## Evidence and reproduction identity

- Remote `main` at freeze: `1e990d55218e3799b999f711a26d50deb3f9b62e`.
- Docker Desktop image: `agent-interface-desktop-integration:local-01`,
  `sha256:44634c6599b9713b382da9937db38d409c9e66bcbce95aaf2bfeae7793c11385`,
  linux/amd64, network none, read-only root, 2 CPUs / 2 GiB / 128 PIDs.
- App: Inkscape 1.4 (`e7c3feb100`) in private Xvfb 1280×800 with Openbox.
- Model: local Ollama 0.20.4 `qwen3.5:4b`, digest
  `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`, Q4_K_M,
  vision capability, temperature 0, seed 2195, JSON output, max 256 tokens.
- Fixture SVG SHA-256:
  `6197766511ca18b75b228bae9db9d4640b9b83549b06008c364d23512fc39fd1`.
- Modal PNG SHA-256:
  `4d1cc87bd6ab8dd21d0cfb1b4265dfc4ae6ef6881642e41b4660a87a575ee4d0`.
- Timeout record SHA-256:
  `d0fcc3bb0c9e427a45bfdc42b9abffb7ba7b14a11c997c89dc0282bd670affa9`.

After the client timed out, Ollama continued consuming CPU. Its process CPU
time increased during read-only polling; the model later unloaded on its own.
No process was killed and no second inference was sent. Preserve the early
setup/capture corrections in `EXECUTION_NOTES.md`; they are not model rows.

## Post-hoc evidence-integrity re-audit

The retained HOLD corpus was re-audited read-only with
[`audit_hold_evidence.ps1`](audit_hold_evidence.ps1). All 18 integrity and
decision-boundary checks passed; the machine-readable result is
[`AUDIT_READ_ONLY.json`](AUDIT_READ_ONLY.json), SHA-256
`f25720cdd7ad12a1418e13b6c0ca783ca1ad8470517b556d1073ac7ac3867d30`.
The auditor source SHA-256 is
`e0c7a34d2f1d2b8fc9de981f41f81fa46cf10fa52b1bf7a2fc23431d5d3f5ca5`.
This validates the retained HOLD records and frozen input identities only; it
does not recover a model response, score a decision row, or upgrade the pilot.

This result should be logged under existing Issue #2195 if/when the evidence is
published. Do not create a local-resource successor issue or claim that
Issue #2195's model-selection hypothesis passed or failed.
