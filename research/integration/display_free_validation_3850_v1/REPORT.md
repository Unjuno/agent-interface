# Display-free static program validation — #4336

## Result and use
PASS_DISPLAY_FREE_VALIDATION_ENGINEERING: the first 36-process engineering matrix
completed with 12 static-valid, 20 static-invalid and 4 input-error outcomes.
The unchanged raw auditor ran 909 checks/errors=[], and all 12 effective record
corruptions were rejected. Sixteen focused unit methods also pass. These are
engineering checks, not GUI/model experiments or a performance/reliability claim.

From the repository root:
```
python -S -B -m runtime.cli_v1.validate_program --program program.json
```
Exit 0 means static validity only; 1 means invalid program; 2 means loading/decoding
error. Every result has side_effect_authority=false, backend_checked=false,
runtime_admission=not_evaluated and task_success=null. Required capabilities are
requirements, not measured backend support. No current dispatcher is changed.

Example: a three-repeat key operation followed by an observe operation with
Boolean w yields INVALID_PROGRAM, detail "observe w must be int",
source_operation_index=1 and expanded_operation_index=3 (both zero-based).
An expiry timestamp of 1 is deliberately statically valid: this command does
not read a clock or grant a live lease. No correction is executed automatically.

## Chronology / fixed inputs
Base46e85863a9d0bfa9f5b7648fd81f3423907ca106.
Source/gate commit66393ef68a98d12eb31d175f5aad2482d79feae1 was published and its12
added files Git-object checked before the retained invocation. FREEZE binds19
executed/source/environment files including8 exact existing core/API/selector
files. Nothing in that frozen set changed after the matrix. One invocation,
36 first cells, no replacements or tuning. Complete fixture input strings and
fixed expectations are in cases.json; exact process outputs are retained.

A separate earlier36-cell development matrix and16 unit methods passed. Its raw
allocation string is the same hard-coded runner label, but its output path,
start/end times and process records are different and explicitly DEVELOPMENT;
it is never pooled with the retained engineering denominator. Its original
71722-byte aggregate is in the conversation download, not the GitHub capsule.
No claim that those development rows were publicly preregistered is made.

## Observations and limits
Both tested environments had WAYLAND_DISPLAY unset; DISPLAY was absent or
:59999. All invocations used CPython3.13.5 -S -B in the supplied Linux container.
Observed socket/subprocess/ctypes-load events and native backend/Xlib/Tk/PIL
modules were empty in all36 inspected validator lifetimes. Input bytes were
unchanged. This instrumentation is not an unbypassable sandbox or a general
hardware no-side-effect proof. There was no native GUI/input/model run.
Docker/OrbStack image attestation is unavailable. Timing is diagnostic only.

The implementation uses existing core validation/expansion and reports only the
first error. It preserves existing unknown-field and ordinary json.loads
semantics; it is not a strict duplicate-key parser or provenance authenticator.
The legacy unhashable-frame TypeError is classified as a generic static-invalid
field rather than escaping; current core code itself is untouched. Inputs are
trusted JSON-like containers/local ordinary files, not adversarial Python
objects/devices. A byte cap is not a wall-clock bound on special files.

The main CLI's subcommand parser and MCP registration are unchanged: this is a
separate runnable module. Packaged zipapp invocation, cross-platform native
behavior, matched-model recovery and token/latency benefit are NOT measured.

## Exact record delivery and one retained publication error
The original engineering records.json is71868 bytes, SHA256
824bc3d1d0a8d0c9d3469a4a5f3b4a9b236538850f652b8800480f4f14dbf96f.
It contains all36 argv/stdout/stderr/exit/trace/input-hash records and source hashes;
cases.json supplies every actual bounded input byte string. Seven zlib/Base64
parts restore the original JSON bytes exactly. This is lossless data encoding,
not regeneration of experimental results. All seven Git blobs were checked.

The first large-text transfer at53d03ddc7cd1b3565b15e15702d39cda3ce5044b was NOT
byte-exact: remote blob7b1039a77612abb57e492b4bf9c2d11d47f8f472 versus local expected
31ed4d585e1ea0973c960a32d3c94d05654ae2a4. It is retained in Git history and marked
superseded in publication_failures; it is never consumed by the verifier. This
was a transport transcription failure, not a tool safety block, experiment
failure or a reason to rerun science. The separate #4331/#4333 blocked source
remains untouched and is not included anywhere in this work.

Read-only reconstruction, source-hash check and exact original audit/control
output reproduction:
```
python -S -B research/integration/display_free_validation_3850_v1/verify_publication.py
```
The packaging-only verifier was written after execution and is not represented
as a frozen scientific auditor. It runs only the original read-only audit and
controls, not the validator/matrix. Temporary decoded data are removed on exit.

## CI / adoption boundaries
The source-frozen dedicated workflow runs the16 new unit methods; its optional
uncompressed-record step does not consume the compressed delivery. A second
additive evidence-only workflow runs the new read-only publication verifier.
No existing workflow or frozen source is changed by that packaging addition.
Local passing checks are not remote CI or independent human review. Merge only
after exact-head applicable checks and scoped review; parent #3850 and the global
ROADMAP remain open. No arbitrary backend capability follows from static-valid.
