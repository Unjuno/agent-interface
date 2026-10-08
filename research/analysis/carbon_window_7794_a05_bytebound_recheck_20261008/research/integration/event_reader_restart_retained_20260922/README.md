# Retained reader restart and checkpoint boundary — Issue #3989

**Retrospective research evidence, not a new formal allocation or production change.**
The original experiments were locally frozen and executed before this Issue existed.
The previous conversation could read GitHub but had no exposed write actions. This
publication preserves that historical STOP and adds the present delivery record;
it does not backdate a GitHub preregistration or rerun any consumed allocation.

Parent: #3876; reader integration: merged #3883; distinct live producer work: #3917.
Original source main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Publication branch was created from observed main
`485f0edc51fee27bf6a8ef21cbfb78612805c4c1` after parallel integration advanced it.
Only this new nested research directory is added. Shared runtime, root roadmap,
predecessor evidence and other workers' branches are unchanged.

## First outcomes retained

| Allocation | Original disposition | Evidence boundary |
|---|---|---|
| v1, 36 planned cases | STOP_EXECUTION_SURFACE_TIMEOUT | Five complete rows; terminal receipt and process exit unavailable. Never pooled with v2. |
| v2, four planned cases | PASS_BOUNDARY_CONFIRMATION_4CELL_SCOPED | All four directed cases, 18 reader CLI calls, six fixture producers and two intentional host SIGKILLs reconcile. One formal invocation; no rerun. |

| v2 case | Retained observation | Interpretation |
|---|---|---|
| Replace file, identical consumed prefix, old epoch/cursor | Changed inode; first new-lifetime record omitted, second returned | Prefix equality does not identify a producer lifetime. |
| Truncate/rewrite, identical prefix, old epoch/cursor | Same inode; same omission | Unchanged inode is not lifetime evidence either. |
| Save response, kill before saving cursor | Three retained, three redelivered, zero missing | This process cut preserves notifications but permits repeated delivery. |
| Save cursor, kill before saving response | Zero retained, zero returned on ordinary resume, three missing | Cursor-first can skip a response not retained by the host. |

Both restart cells also retain new-epoch/old-cursor refusal, new-epoch/no-cursor
full recovery, and changed-consumed-prefix refusal. Reader responses remain
`authority=none`, `acknowledged=false`, `input_dispatched=false`.
The original stream retains its bytes: missing notifications are not physical
deletion or irrecoverable loss. Redelivery is not observed model consumption or
execution of a task twice. The existing HOST_CONTRACT already predicts these
constraints; this is directed confirmation, not a newly discovered upstream defect.

## H / T / D / C / U

**H.** A caller epoch and equal prefix cannot distinguish a new producer lifetime;
response/cursor persistence order determines omission versus redelivery at the
tested between-store process-kill cut.

**T.** Two producer-restart cases and two host-store cases; exact existing
DeliveryLedger.prepare and passive-reader module CLI in separate processes.
Four construction cells excluded; original v1 STOP unchanged. New formal
invocations in this publication session: zero.

**D.** Scoped PASS requires all four original cases, bytes, cursors, process
receipts, neutral authority and independent raw reconstruction to agree.
The original 12 evidence corruption controls must reject. Missing v1 terminal
receipts remain STOP regardless of the interpretable partial rows.

**C.** Provided Linux x86_64 execution container, CPython 3.13.5, standard library.
Docker/OrbStack CLI and image identity unavailable. No model/provider, GUI/input,
real task, experiment-network call or production queue. Source snapshots are
Git-object verified, not a complete repository checkout. An independent auditor
means a separate implementation/process by the same author, not external review.

**U.** Four directed cases do not estimate reliability. Persistent producer epochs,
ACK/model viewing, real producer/host integration, multiple consumers, power-loss
durability, useful-feedback timing and token/task benefit remain untested here.
No component result completes #3876 or the global ROADMAP. Broader related work
#3931, #3933, #3941, #3977 and #3978 remains separate; do not repeat their allocations.

## Lossless evidence and source identities

The eight base64 parts reconstruct a bounded XZ-compressed UTF-8 JSON map of
**173 exact original files, 522,570 file-content bytes**, with original paths.
The map contains source, plans/freezes, raw/process bytes, construction, audits,
STOP records, and the original unposted Issue/PR drafts. Those drafts and the old
`STOP_GITHUB_WRITE_TOOL_UNAVAILABLE` describe historical state, not this publication.
Nothing inside either original directory was edited to change that state.

- Compressed: 47,900 bytes; SHA-256 `9b466fba115ab8fa322b5fd216c60e546fc8acc22c937cd169ed8aeb80a50aec`.
- v2 raw: 62,049 bytes; SHA-256 `9fff7584a3092143e619e8d60e5a4e4f74771f32e3bc637ef1fcc37b41705db5`.
- Original audit stdout: SHA-256 `90bfc03cbb797789227cf742e2c96af02b5dc103ca64f94759a3fd6a1531a906`.
- Original reader blob: `ea72c166c2cea511ea91031dfbb14563fe4e3245`.
- Original CLI blob: `1a97a659113666ccaa254ab2bf5dc0306e217015`.
- Original DeliveryLedger blob: `fb50be9d4d821a7836e6a0158c53a983f0f91df5`.

MANIFEST.json binds part order, exact part bytes/Git object IDs, compressed/map
hashes and member totals. Hashes check integrity, not publisher authenticity.

## Restore and re-audit without executing an experiment

Use Python 3.10 or later with the standard lzma module and an absent destination
beneath a trusted private directory. The helper validates the bounded archive,
rejects invalid paths and existing destinations, then writes non-executable data.
Do not run the retained formal runners or remove their consumed-allocation markers.

```bash
python research/integration/event_reader_restart_retained_20260922/unpack.py /tmp/reader3989
v2=/tmp/reader3989/research/integration/event_reader_restart_checkpoint_bounded_20260922_v2
PYTHONDONTWRITEBYTECODE=1 python "$v2/audit_bounded.py" "$v2/evidence/formal-01"
PYTHONDONTWRITEBYTECODE=1 python "$v2/test_bounded_audit.py" "$v2/evidence/formal-01"
```

`test_publication.py` restores to a temporary directory, checks all bytes, checks
eight invalid-publication conditions, and invokes only these two retained auditors.
It does not invoke a producer, formal runner, model, GUI, or native input.

## Revalidation and delivery gate

Original SHA256SUMS: v1 99 entries, v2 72 entries, all matching (the two manifests
exclude themselves). Re-audit stdout is byte-identical to the original audit;
12/12 original corruption controls reject. A second archive restoration preserved
all 173 files, and the 11 publication checks passed, including eight refusals and
both restored-auditor output identities. See REVALIDATION.json for exact commands,
outputs and scope. Repository-wide tests were not run; remote CI/review is separate.

Delivery sequence: source/raw restoration -> independent re-audit -> bounded
archive validation -> Git blob readback -> reviewable research-only PR -> inspect
checks/reviews -> main readback only after a permitted merge -> clean only the
owned branch after dependency review. Publishing evidence is not runtime adoption.
A later live owner/host integration must explicitly bind producer lifetimes and
retain response before cursor progress; notification retention must remain separate
from consumption ACK and action replay authority.
