# #5139 current-main dataset construction composition check

## Disposition

`PASS_DATASET_SAMPLER_AUDIT_CONSTRUCTION_ONLY` on the current-main successor
branch. This is a bounded, synthetic CPU construction experiment. It is not
the formal allocation, does not consume a formal seed, and is not a model,
CUDA, Docker, GPU, LoRA, quality, or safety result.

## H / T / D / C / U

- **H:** the #5139 dataset generator, with a separately supplied
  `support_seed`, emits both 32-row support arms from one 128-row pool using
  the frozen class-conditional ranking; the independent stdlib auditor can
  reconstruct the selections; changing only the formal/held-out seed leaves
  support rows unchanged.
- **T:** generate the complete synthetic support and held-out pools with two
  explicit test-only seed sentinels; independently audit selected row IDs and
  full row values; test count/split invariants; mutate the support seed and
  verify rejection. No optimizer/model imports or external service calls.
- **D:** `PASS_DATASET_SAMPLER_AUDIT_CONSTRUCTION_ONLY` iff generator output
  passes the raw selection oracle, the support and held-out sizes are
  128/256 with 32 rows per arm and 64 held-out rows, split IDs/scopes/tasks
  remain disjoint, formal-seed-only change preserves the support pool/arms,
  and a changed support seed is rejected. All three new checks passed.
- **C:** one deterministic synthetic protocol and a single construction-only
  sentinel pair; this does not test data representativeness, model behavior, or
  whether the original study hypothesis is true.
- **U:** one Windows/Python 3.11.9 host and one synthetic generator. No
  pinning/build gate, formal raw-training auditor, task-effect claim, GPU
  envelope, generalization, or product claim follows.

## Frozen identities and source lineage

- Current-main parent: `7be3499f515636875edbe071ec127fcc88714220`.
- Clean additive branch: `research/qwen5139-current-main-prep-20260928`.
- `protocol.py` SHA-256:
  `3d324897c9e99abe453ed500c486780243efe9fcff87441197471b5b47d665b6`.
  This matches the preserved #5014 v2 frozen protocol source; its old study
  allocation, input, seed, fit, and result are not reused.
- `sampler.py` SHA-256:
  `0cdbe3e5b61202ec6ea5bd8810f4734a85141e7a7cbaf22ce886568b0f2c23a6`.
- `audit_sampler.py` SHA-256:
  `26007eee3d9402842953618fc2225c200b2f3ad8ab61d49be93840fd84e68638`.
- Generator: `make_dataset.py`; it requires explicit independent formal and
  support seeds and a caller-supplied allocation label. Tests use only
  `73194111`, `73194112`, and `51829177`, marked synthetic construction
  sentinels. These are not proposed or frozen allocation seeds.

## Executed commands and results

On host Python 3.11.9:

```text
python -m unittest discover -s research\experiments\qwen05b_abstention_balance_5139_sampler_v1 -p 'test_*.py' -v
Ran 16 tests in 0.034s — OK

python -m py_compile research\experiments\qwen05b_abstention_balance_5139_sampler_v1\protocol.py research\experiments\qwen05b_abstention_balance_5139_sampler_v1\sampler.py research\experiments\qwen05b_abstention_balance_5139_sampler_v1\make_dataset.py research\experiments\qwen05b_abstention_balance_5139_sampler_v1\audit_sampler.py
exit 0
```

The 16 tests comprise six candidate sampler tests, seven independent sampler
auditor tests, and three generator/auditor composition tests. The composition
checks reconstructed the complete 128-row support pool and 256-row held-out
pool, selected exactly 32 rows per arm and 64 held-out rows, verified split
disjointness, checked support invariance under formal-seed-only change, and
rejected a changed support seed. No package installation occurred.

## Failures and gates not exercised

An initial attempt to materialize these files in the clean current-main
checkout targeted a path that did not yet exist; it failed before test
collection and wrote no files. The package was then added under the correct
checkout-relative path and the commands above passed. The earlier PR-branch
topology concern is documented separately in PR #5155; no old branch history
was merged or rewritten.

Still mandatory before any training: fresh source/data/model/tokenizer and
image freeze; complete construction image and separate raw-output auditor
gates; seed/output collision checks; resolution of the historical
`sad_cannon` invocation ambiguity; current local process/container/GPU
inventory; and an exact, named #5139 GPU/Docker lease. This check satisfies
none of those gates. No model load, CUDA initialization, Docker command,
training, adapter write, or GPU allocation was attempted.
