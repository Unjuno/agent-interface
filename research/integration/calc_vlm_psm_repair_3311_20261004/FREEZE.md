# G23 candidate freeze

Run ID: `CALC-VLM-PSM-REPAIR-3311-20261004-G23`

This experiment tests one narrow repair seam: whether a requested vision-language model can resolve four cells that the frozen G21 OCR-consensus procedure abstained on. These are development examples from the existing G20 corpus, not held-out evidence.

## Frozen inputs

The source frames are copied byte-for-byte from G20. Each crop uses the existing G21 ROI rule: crop `88x14` at the listed screenshot origin, grayscale, nearest-neighbor 4x resize, then a 20-pixel white border.

| Attachment | G20 source frame | ROI origin | Source SHA-256 | Crop SHA-256 |
|---|---|---:|---|---|
| `repair-01.png` | `calc-compiled-ocrlive-4d74-1.png` | `127,161` | `b0e451fdbaf7729e96323bfa0ed5952a6cb99c266903714eafd10ccc260fdb58` | `8ff56201d9ce921189b054f842ea2a0b55cb5a0b851e104ac041d0911d7ed919` |
| `repair-02.png` | `calc-compiled-digits-4d74-1.png` | `127,161` | `edaf13819de1f67fee35e29be0ea9d8a6bd22a9920f7066367ac719cf9a5d032` | `8ff56201d9ce921189b054f842ea2a0b55cb5a0b851e104ac041d0911d7ed919` |
| `repair-03.png` | `calc-compiled-digitunavailable-4d74-1.png` | `127,161` | `34a81314efb7dbec3943a3f749959a903ddce7a7687709f84cd33800eff65f8f` | `8ff56201d9ce921189b054f842ea2a0b55cb5a0b851e104ac041d0911d7ed919` |
| `repair-04.png` | `calc-measured-boundedread-4d74-1.png` | `217,161` | `edd2427dd66b8d57e65c037a1935a1ca413eea6952448c86bb8f5d1213ea4439` | `11a6fcba5a2ab6357e0385648a44f1b7efabbfd2c0c6c46e7db7b5a496873fd0` |

Prompt file SHA-256: `880fe52cefd86e7c585b371e8ad6277a426a37b4cfa87bc990e08535f27a3134`.

Oracle labels and its source sidecar are kept under ignored `private/` and are not candidate context. Expected outcomes do not participate in crop selection or prompt construction.

## Frozen invocation

The sole model attempt is `python3 run_once.py`. The launcher invokes one `codex exec --json --ephemeral --ignore-user-config --skip-git-repo-check -C /tmp -s read-only -m gpt-6.1-sol -c model_reasoning_effort=medium` command with exactly the four listed images and the exact contents of `PROMPT.txt`. It saves raw stdout, stderr, and a hash receipt under ignored `private/`. Its exclusive attempt marker is written before launch; any outcome prevents another invocation.

No repository context is supplied to the model. The request is read-only and asks for a JSON array of exactly four digit strings or nulls, with null required for ambiguity.

## Decision gate

PASS only if the single invocation exits zero, produces one completed assistant final response, and that response parses as exactly four strings/nulls that all match the four independently frozen oracle labels. Any malformed output, null, wrong value, missing final response, or invocation failure is FAIL or STOP and is not retried. A passing result supports only an in-sample, four-cell model-assisted repair observation; it does not establish held-out accuracy, live desktop effects, task success, speed, or a generally safe fallback.

The crop script, prompt, inputs, and this freeze must be committed before the attempt. The resulting commit hash is recorded in `REPORT.md`.
