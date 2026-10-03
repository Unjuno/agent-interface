# A14: image-only first-character review — retained H_FAIL

The first frozen four-condition experiment completed, with method evidence valid
but the prospective review hypothesis false:
`METHOD_PASS_FINITE_REVIEW_ONLY / H_FAIL_FINITE_REVIEW_ONLY`.
This is a finite counterexample to accepting an image-only review verdict as
task correctness or input authority, not a general model reliability estimate.

| Condition | Actual TARGET / DECOY | Required answer | First model answer | Exact |
|---|---|---|---|---|
| exact | hbk / empty | NO_REPAIR | NO_REPAIR, TARGET hbk | yes |
| missing prefix | dv / empty, requested hdv | INSERT_PREFIX h | NO_REPAIR, TARGET hdv | **no** |
| wrong recipient | empty / hql | REFUSE | REFUSE, DECOY hql | yes |
| ambiguous error | zr / empty, requested hcr | REFUSE | REFUSE, TARGET zr | yes |

All four observations were actual private Tk/XTest screens in a pinned WSLc
container. Independent audit binds delivered key events, actual app fields,
geometry, clocks, original XWD and pixel-identical PNG, model image/prompt,
raw CLI streams, request receipts and reported usage. It does not identify why
the model misread the missing-prefix screen.
The apps ended before host model review; no answer triggered input, repair,
Save or a task file. A response to an old screenshot is not fresh action authority.

## Revalidate without repeating the experiment

From this directory:

```sh
python -B -m unittest discover -v
python -B verify_packet.py
```

The data-only verifier returns `PASS_RETAINED_H_FAIL_ONLY`, not H_PASS.
It checks all 72 original retained files against RETENTION, nineteen frozen
source hashes, eleven byte-identical inherited A13 files, all four semantic
audits, the original audit hash and reconstruction, all three outer process
receipts/bindings, and complete SHA256SUMS coverage. Original A13 STOP is untouched.
Header tampering, lost streams, hypothesis promotion, model authority, every
row's clock corruption and unsafe/duplicate/incomplete manifests are tested.

Seventeen tests pass with a private Linux Xvfb/Openbox display. Without an actual
private Linux display the single construction test is explicitly skipped;
Windows has 16 PASS + 1 SKIP. CI is data-only and uses the same explicit skip.
The display construction test is a separate temporary hzx/zx fixture, not a
formal A14 row or model call. No revalidator launches the formal allocation.

## Handoff and next research gate

See [PLAN.md](PLAN.md) for prospective roadmap/H/T/D/C/U, [FREEZE.json](FREEZE.json)
for exact frozen commands/source hashes, and [RUN.md](RUN.md) for the first ledger.
Issue [#5260](https://github.com/Unjuno/agent-interface/issues/5260) retains
prospective comment 5973281561 and first result comment 5973297464.
The result package is additive, suitable for independent integration, not a
runtime promotion or closure of #5260/#59/the full roadmap.

Next: separately freeze a live composition in which model suggestions must
agree with a later current local observation and an independent task/file
endpoint before task success. A wrong NO_REPAIR must not falsely finish a task;
wrong recipient, ambiguous text or drift must YIELD without task input.
Measure any actual recovery and model wait, keeping the same requested model.
Do not retry this consumed allocation, reinterpret A13, or invent a cause for
the original missing-character fault from these controlled fixtures.

## Cost and scope

Four first requests used the frozen host codex-cli0.160.0, requested
gpt-5.6-luna/low and identical A13 prompt/schema. Server model identity is not
independently attested. Total column sums are input 55,132; cached input 12,032;
cache-write input 0; output 253; reasoning output 118. These fields are retained
separately, not additive billing totals. Request wall sums 26.0293195s differ
from outer model phase 27.6921673s. No price, causal speed/token ranking,
held-out accuracy rate, recovery efficacy, physical release or human-tempo claim.
GUI/auditor containers use network-none; host cloud review does not.
WSL swap/cgroup and CLI PowerShell warnings are retained. Requested CPU/memory
flags do not prove enforcement, OOM remediation or faster iteration.
