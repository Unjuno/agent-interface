# formal06 — finite paired method PASS; one changed-evidence recovery observed

Allocation: `5260-a15-model-paired-formal06-20261004`  
Frozen source commit: `206d7e777bb49c6af7f925b131f2b508bed6c317`  
Plan SHA-256: `dbf2cbd1b282c73a42bc8ea724d0810d94e82f0b1f9babb62e07ffa3508e0a90`  
Outer-plan SHA-256: `db729233696a406aed2e76531e54af54814fa1d667989636d1a47ac205c1fdb8`

## H / T / D / C / U disposition

- **H:** The retained A14 visual counterexample reappeared on the first model
  response: the live target contained `dv`, the exact requested target was
  `hdv`, and the model reported `observed_target=hdv`, `decision=NO_REPAIR`.
  The guard rejected that stale response with `MODEL_STATE_MISMATCH`; after a
  newly captured image, one recovery response reported `dv` and proposed only
  the missing `h`. The guarded path produced exact `hdv`. This is one finite
  success on the specific counterexample, not a reliability estimate.
- **T:** Four fresh control/guard pairs. Four shared first model calls, plus
  exactly one changed-evidence recovery call for pair-001. Total actual CLI
  calls: five; no retries or row replacements.
- **D:** Independent file-only scores: control 2 `EXACT_FILE`, 1 `WRONG_FILE`
  (`dv` where `hdv` was requested), 1 `UNFINISHED_NO_FILE`; guard 3
  `EXACT_FILE`, 1 `UNFINISHED_NO_FILE`. Wrong-recipient events: zero in both
  arms; decoy changes: zero. Pair-002 refusal is unfinished, not success.
- **C:** First answer and host bytes retained. The guard admitted no native
  input under the mismatched first answer; the recovery used a fresh current
  app snapshot and reconstructed complete prompt. Every first/recovery slot,
  both outer-launch byte receipts, frozen source capsule and source/model/
  schema/command joins passed the independent audit.
- **U:** Preserve the exact packet and add this bounded result to #5260 through
  the batched branch/PR update. Keep the broader first-character timing and
  integrated-path questions open.

## Formal execution and audit

Requested CLI model/effort were `gpt-5.6-luna` / `low`; identity is not
independently attested. The run used WSLc image
`sha256:a67fdc7786a9245adf081382c35dfdee2d3e8506859d397972750428aede6461`,
network `none`, non-root UID 65534, a read-only source mount and a 512 MB memory
request. WSLc reported that the host kernel cannot apply swap limits; therefore
no memory-plus-swap bound is claimed.

The independent paired saved-custody audit exited 0 with
`METHOD_PASS_FINITE_LOCAL`, `gaps=[]`, five CLI calls and no provider-performance
claim. The separate file auditor exited 0 with `method_audit_complete=false`
and no provider-performance claim; its limited per-file outcomes are above.
Full audit JSON, exact outer process attempts/receipts/streams, raw model
responses, app/native records, plans, images and source capsule are retained in
this allocation. Cooperative retained custody is not cryptographic server or
model attestation.

## Scope limit

One finite four-pair WSLc/Tk study establishes that this guarded path can detect
and recover from this specific same-model wrong visual observation while the
unprotected control saves the wrong file. It does not establish that a 50 ms
wait caused #5260's original missing character, that any delay is optimal, or
that recovery generalizes to other tasks, apps, models or environments. Do not
close #5260 or #57/#59 on this result alone; continue the roadmap with the
current-main integration evidence and remaining planned work.
