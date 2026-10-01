# #59 per-key occupancy ledger — host-only T0

## H / T / D / C / U

- **H:** A per-key press/release ledger bound to one action and epoch can yield conservative server-processing occupancy bounds; missing or inconsistent receipts must yield `UNKNOWN`, never a duration inferred from the outer program envelope.
- **T:** One deterministic synthetic two-key overlap ledger; run the candidate once, then a separate raw-only auditor once. Apply five evidence corruptions inside the auditor. No retry.
- **D:** `PASS_METHOD_SCOPED` only if the auditor independently reproduces `SPACE=32..50 ns` and `W=70..90 ns`, binds one verified-empty terminal receipt, and rejects all five corruptions. This is a construction test, not live occupancy.
- **C:** Windows host, stdlib Python only; no Docker/X11/GUI/input/model/GPU/network. Docker Desktop service was stopped and the user-level service-start attempt did not start it. This host-only rung does not consume the separately requested #59 live T1 Docker slot.
- **U:** XSync brackets processing, not application delivery or task usefulness; keymap snapshots are discrete; no live key hold, safety, effect, latency, MAP01, or human-tempo claim follows.

The lower bound for a key is `release_request_ns - press_sync_ns`; the upper bound is `release_sync_ns - press_request_ns`. These bounds assume a single owner and no unlogged external input. The candidate does not aggregate overlapping per-key intervals into a continuous-control claim.

## Run

```powershell
python -m unittest discover -s . -p 'test_*.py' -v
python run_candidate.py
python audit.py
```

Allocation label: `MAP01-PER-KEY-OCCUPANCY-LEDGER-59-T0-20261001-01` (host-only construction; no shared-container lease). Main freeze: `6cd70ad4bfad74e11658057bf024918bffb24add`.

## First outcome

On 2026-10-01, Windows host Python 3.11.9 ran the candidate once and a separate raw-only auditor once. The auditor returned `PASS_METHOD_SCOPED`; it reconstructed `SPACE=32..50 ns`, `W=70..90 ns`, and rejected all five declared evidence corruptions. The six host tests pass. The raw and audit JSON are retained under `results/t0-01/`.

Provenance caveat: the H/T/D/C/U description and deterministic fixture were written before the candidate invocation, but the complete source-hash manifest was generated after the first outcome. This is therefore an exploratory host-only construction result, not a prospectively source-hash-frozen formal allocation. No rerun was made. The first outcome is preserved as-is; any stronger successor needs a new allocation identity and a pre-run hash freeze.
