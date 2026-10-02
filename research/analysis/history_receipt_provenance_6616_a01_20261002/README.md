# #6616 invocation-bound provenance T0 A01

## H / T / D / C / U

- **H:** A fail-closed lifecycle classifier can distinguish an actually receipted candidate/audit pair from output files that appear without invocation receipts, while preserving pre-run and partial states.
- **T:** A finite five-row synthetic lifecycle corpus exercises completed, output-without-receipt, candidate-only, candidate/audit hash mismatch, and true pre-run states. Run a deterministic candidate once and a separate raw-only auditor once in distinct, digest-pinned OrbStack containers. No model, GUI, participant, host-user files, network, or external effects.
- **D:** `PASS_METHOD_SCOPED` only if all five lifecycle states and invocation counts are reconstructed exactly, output without a candidate receipt cannot be called complete, and candidate/auditor hash disagreement is held. Any false completion is `FAIL_METHOD`; malformed or missing evidence is `HOLD`.
- **C:** The synthetic receipts are authored, not cryptographically authenticated; this tests lifecycle semantics, not resistance to forged host receipts.
- **U:** No human reliance outcome or trust effect, real subprocess provenance, GUI behavior, or production protocol claim. #6616's existing inconsistent local allocation remains untouched and unresolved.

## Frozen inputs and procedure

This additive successor uses a new allocation ID and directory; predecessor files/outcomes are not inputs and are not changed. All five fixture rows are explicit finite cases. The candidate consumes only the fixture; the independent auditor consumes fixture plus candidate raw output and does not import candidate code. Container outputs are separate from read-only sources. Formal invocation count is one candidate and one auditor, with no retry. The initial local unit tests are construction checks and do not count as the formal result.

## Result

Formal disposition: `STOP_CONTAINER_SOURCE_MOUNT_EMPTY`. One candidate container started and exited 2 before reading the fixture; auditor=0, retries=0. Full preserved details are in `RUN_RECORD.md`. This is infrastructure evidence only, not a scientific result.
