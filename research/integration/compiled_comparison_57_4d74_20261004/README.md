# Full matched Chromium comparison — #57 A05

Current fixed compiled candidate: **REJECT on correctness** (9/12 exact task submissions). A/B/D each12/12. This rejects the declared crop-OCR/template candidate on this fixture; it does not reject compiled interfaces in general.

| Block | Arm | Exact tasks | Task models | Task input | Task output | Task elapsed s | OCR calls |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | A | 6/6 | 6 | 81054 | 508 | 56.666 | 0 |
| 1 | B | 6/6 | 2 | 27018 | 172 | 47.962 | 0 |
| 1 | C | 4/6 | 2 | 27100 | 197 | 62.420 | 16 |
| 1 | D | 6/6 | 0 | 0 | 0 | 13.891 | 0 |
| 2 | D | 6/6 | 0 | 0 | 0 | 15.873 | 0 |
| 2 | C | 5/6 | 2 | 27100 | 195 | 63.069 | 17 |
| 2 | B | 6/6 | 2 | 27018 | 171 | 48.782 | 0 |
| 2 | A | 6/6 | 6 | 81054 | 508 | 56.950 | 0 |

A=fresh image grounding each task; B=checked retained target plus actual model repair; C=same caller with bounded compiled graph/exact crop OCR; D=known-form autofocus keyboard. Same six tasks/seeds within each block, orders ABCD/DCBA. C failed block1 tasks5/6 and block2 task6 before Submit after exact OCR mismatch; partial typed content is preserved, never retried or regraded. Independent oracle reports zero duplicate/unexpected submissions. B model schedule is1/0/0/1/0/0 each block.

Elapsed totals cover task navigation/source/grounding/check/input/verification. They exclude schema preflight, process startup and final independent scoring; provider wait is already inside task elapsed and must not be added again. Task costs in the table exclude separately retained schema preflights. All26 real provider attempts including6 preflights total input343542/output2040; cached245248 is an input subset and reasoning1288 an output subset. Cache-write input0. Monetary cost UNKNOWN. Human setup cost UNAVAILABLE. OCR calls/elapsed, native programs/observations, mint/check receipts and journal storage are retained separately in the machine report; no complete end-to-end economic or population efficiency inference.

D is cheaper and fully successful on this known fixture, but uses human-known form/autofocus behavior. B reduces task model calls versus A in both blocks with equal fixture correctness; scope stays these two descriptive replicates. C fails the correctness hard gate and is slower than B in both blocks; do not claim efficiency from its lower completed work. Method enum selects a fixed template and does not test free-form planner generation. Fixed OCR crops are not a general field detector.

## Provenance and first outcomes

- A01: target aliases lost across copied callback payload; author stopped after failures. All20 provider attempts preserved.
- A02 / #7392: minted-target return repaired; stopped on missing repair mint_records at task4. All10 provider attempts preserved; B independent scorer unavailable.
- A03 / #7398: post-model checked-target return repaired; A6exact/B5exact, stopped at256-frame journal capacity; unresolved pending preserved, never reset/recovered. All10 provider attempts preserved.
- A04 / #7403: capacity backend passed journal construction regression, but relocated client socket path failed before task startup. One actual preflight preserved.
- A05 / #7406: socket location resolved without importing side-effectful script; actual startup/no-action scorer regression passed, fresh formal48-task comparison completed.

All allocations use frozen main13bab54ea6d91978247ecc1b70e5060db752367a, 1645 Python-file closure retained once under source/. Original FREEZE/SOURCE/protocol files are byte-preserved. Each formal-output retains launch argv/stdout/stderr/HOST/provider requests and responses/raw CLI events/images/task rows; A01 AUTHOR_STOP and A02–A04 STOP files remain first outcomes. A05 has no STOP. WSLc image digest4ebbb04fd31e2833ac6c66ddbb9a03351904f34716e55d45d220d28553004601 and actual CLI digest/version pinned in protocols. WSL kernel warned swap limits unavailable; configuration is not proof of enforced isolation. No GPU needed for this CPU/X11/Chromium comparison.

A05 named capacity modules change only1024frames/64MiB and socket script location versus the source client. Hash chain/flock/per-frame1MiB/no-reset/no-compaction remain. Same backend for all arms. The capacity and startup regressions are construction evidence, not scientific successes. Saved OCR qualification is post-run development evidence and its B failure was disclosed before A04/A05 launch.

## Audit and reproduction

The post-run author audit is limited to frozen identity, provider config/image/schema/usage joins, independent HTTP scoring, all-task retention and native empty release. It is not a preregistered auditor, current-main runtime qualification, full authority proof, collateral-content audit, product acceptance or human-speed test. Reproduce without GUI/provider calls:

```text
python retained_evidence_audit.py a05 source
python retained_evidence_audit.py a03 source
python retained_evidence_audit.py a04 source
```

The same script cannot assume interrupted A01 or unavailable A02 evidence is complete; preserve uncovered joins as uncertainty, not fabricated zeros. FILES.json hashes every retained member except README/FILES/.gitattributes. Fresh independent reviewer and PR checks are required before merge. Applicable local #3270 replay gate2tests passed in WSLc; that unrelated gate does not establish task efficacy.

Next research decision: do not spend more formal allocations tuning this fixed OCR candidate under the same question. Integrate the full failure/result, compare roadmap #56/#57 requirements and peer #7353 source-bound audit, then select a genuinely unresolved transfer or planner-generated interface question under its owner. Second-domain transfer, general efficiency, human tempo and full roadmap remain unverified.
