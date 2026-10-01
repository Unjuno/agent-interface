# Display-free static validation — #4336, parent #3850

## Question and scope
Can a caller inspect an unexecuted program through an ordinary Python module CLI,
using the current contract/compiler, without requiring a display or importing a
native backend? This is a bounded engineering verification, not a new model/GUI
experiment or proof of the runtime's correctness. Main at intake:
`46e85863a9d0bfa9f5b7648fd81f3423907ca106`.

Own new `runtime/cli_v1/validate_program.py`, `test_validate_program.py`, this study
directory and one new `.github/workflows/runtime-static-validation-v1.yml`.
The CI file is a pre-allocation scope addition: existing CLI CI enumerates test
modules explicitly and would not execute the new tests. No existing file is
modified. #4331/#4333's blocked source and capsule are NOT reused or republished.
Bounded live Issue/PR/branch searches cannot reveal unpublished work.

## H
The exact existing static contract and sequence expanders can return useful,
bounded diagnostics without opening a native backend. Source indices must still
refer to the original operations after expansion. Static validity is neither
runtime admission nor task success. An expired positive timestamp is a required
static-valid negative control for that distinction.

## T
18 cases in cases.json, in two environments: DISPLAY absent or DISPLAY=:59999;
WAYLAND_DISPLAY absent in both. 36 fresh CPython -S -B processes, one invocation
per cell, no retries or replacements. Each invokes the actual module as __main__
through runpy with ordinary argparse arguments. An observational sys audit hook
records socket/subprocess/ctypes-open events; sys.modules records native backend,
Xlib/Tk/Pillow imports. This is instrumentation, NOT a security sandbox or a
complete hardware side-effect monitor. Plain `python -m ...` is separately tested
by the unit suite. No backend stub, native input, GUI, model or network experiment.

Inputs cover minimum release-only with expired lease; normal observe; region and
width/height mistakes; Boolean width; repeated keys; text gaps; mixed expansion;
source index mapping; 128/129 operation boundary; missing terminal release;
unsupported operation; invalid frame type; malformed JSON; missing file; nonobject.
The old core can raise TypeError for an unhashable field: the new facade classifies
that as static invalid with generic bounded detail, without altering the core.
It does not claim identical exception taxonomy to dispatch for that case.

Development/unit and a development matrix are retained separately. Freeze final
source, fixtures, auditor and controls publicly, with exact Git-object readback,
before the retained engineering matrix. Source/environment hashes, all input text,
stdout/stderr, actual exit codes, module/event instrumentation and process identity
are retained. Expected results in cases.json are authored before candidate matrix
outputs. The independent auditor does not import candidate, runner or core.

## D
PASS_DISPLAY_FREE_VALIDATION_ENGINEERING only with all 36 ordered cells; exact
predeclared verdict/category/index/count fields; exits 0/1/2 as specified; no task
text in diagnostics; input bytes unchanged; no observed native imports or watched
side-effect events; every output explicitly non-authoritative and task_success=null;
source hashes unchanged; and all 12 effective recorded-output mutations rejected.
Expected 12 static-valid, 20 static-invalid, 4 input-error outcomes, NOT 12 task
successes. Any discrepancy is engineering FAIL/HOLD; incomplete/process/source
records are STOP/HOLD. Never tune a frozen gate into a first-pass result.

## C/U
No performance, natural error frequency, model correction, GUI success or full
admission result. A future compiler change could cause parity drift; this path calls
the same two expansion functions in dispatch's current gap-before-repeat order.
Only first error is reported. Unknown fields and ordinary json.loads semantics
remain as in the existing system; duplicate-member/raw-JSON authenticity is not
addressed. inspect_program expects trusted JSON-like Python containers, not objects
with custom methods. inspect_file is for local ordinary files; byte cap is not a
wall-clock guarantee for devices/pipes. Input file reads are not atomic snapshots.
No schema upgrade, target lookup, lease minting, permission grant or automatic fix.

No Docker executable/image identity is available; actual supplied Linux container
and CPython are recorded. No site dependencies are required by the inspected path.
Same-author separate audit is not independent human review. No calibrated combined
uncertainty or coverage factor is inferred from discrete deterministic checks.

## Variables and derivation
|Symbol|意味（日本語）|SI単位|定義|範囲・前提|型|
|---|---|---|---|---|---|
|p|入力プログラム|1|JSONで表現する既存program-v1|普通のJSON値|辞書/スカラー|
|e|展開後のプログラム|1|既存compilerを順に適用した複製|最大128操作|辞書|
|i|展開後の操作位置|1|coreが返すoperation_index|0..127、位置が分かる時だけ|整数スカラー|
|j|元の操作位置|1|compilerのsource_operation_index、未展開ならi|元opsの範囲内|整数スカラー|
|n|保持する工程ケース数|1|18条件を2環境で実行した数|事前固定36|整数スカラー|
|t|プロセスの単調時計値|s、rawはns|同一ホストのmonotonic_ns|前後順序だけを評価|整数スカラー|

The facade copies p, applies the same selected compiler as dispatch, and calls the
existing validator on e. Thus acceptance for the tested ordinary JSON values uses
the same contract; no backend capability is inferred because no backend manifest or
current-world arguments are evaluated. For expanded operations, each compiler
emission retains its original source position; mapping i through that list yields
j. For unexpanded input the positions coincide. Tests explicitly exercise three
emissions from one source operation before a later malformed operation.

Unit check: indices/counts are dimensionless; timestamps compare only one host's
nanoseconds. No runtime expiry comparison is made, deliberately: a schema-valid
expiry value is not evidence of an unexpired lease.

## Roadmap
Existing-source parity -> implementation/unit checks -> development harness ->
public exact source/gate freeze -> one 36-cell engineering matrix -> independent
raw audit and 12 controls -> full plain-text evidence PR -> applicable exact-head
checks/review -> qualified main integration/readback. Parent #3850 and global
ROADMAP remain open. Do not rerun old allocations to obtain a more useful result.

## Primary specifications
Python 3.13 json documentation: https://docs.python.org/3.13/library/json.html
Python sys audit API: https://docs.python.org/3.13/library/sys.html#sys.addaudithook
Repository core/sequence/API at the intake SHA (BASELINE_BLOBS.json).
