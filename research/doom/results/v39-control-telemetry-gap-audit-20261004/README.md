# v39 control telemetry gap audit

## Question and result

**H:** The retained current-main v39 stream can identify per-key admission and key-up/release transitions, and its observation records can identify independently useful feedback.

**T:** Inventory all immutable v39 `events.jsonl` records and the paired `owner-events.json`; compare per-key admission, aggregate hold acknowledgements, owner release receipts, direct key-up/release events, and observation semantics. Stop if the pinned source bytes or expected row shapes differ.

**D:** `PASS_RAW_SCHEMA_INVENTORY_SCOPED` means the pinned inventory is internally consistent. The specific observability hypothesis fails for this trace: 39 per-key admission rows have admission/ack clocks but no intent/program/step identity; 28 aggregate `keys_held` records do carry program/step and key set; 13 owner records report verified empty input; neither stream has a key-up event or per-key release bracket. All 218 observation records mark semantic completion `unknown`.

**C:** These event receipts describe software-side admissions and owner/X-server state checks. They do not prove a physical keyboard transition, target application receipt, or useful task effect.

**U:** This is an offline schema inventory of one retained v39 trajectory. It is not an experiment replay, matched control, physical occupancy measurement, recovery-efficacy result, or runtime-code change.

## Provenance

All inputs are byte-for-byte files from public main commit `0ba1ef384965267c38a120f61977953636220fd3`:

- `events.jsonl` — SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`
- `owner-events.json` — SHA-256 `cdf628825312e6eb0cd810f7d0b3a77e52c1c2f646099bc07a34b4e3a90c08b7`
- `sources.json` — SHA-256 `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`

Run `python -B audit.py` to recompute `audit.json` from these saved bytes. The script verifies each input digest before analysis. The next useful instrumentation revision should bind a stable occurrence/intent/program-step ID through each key's admission and release bracket, preserve per-key monotonic request/sync clocks, and label server-keymap witnesses as server-state evidence. The matched live experiment must separately preregister an independent task-effect feedback predicate and bounded-recovery decision rule.
Integrity: `SHA256SUMS.txt` covers the six analysis inputs/code/result files. Verify with `python -B verify_manifest.py`.
