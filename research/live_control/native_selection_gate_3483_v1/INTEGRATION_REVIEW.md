# Integration review

Recovered from PR #3490, exact source head
`805cddb7193f533c096b3ee8bda3a0ee4ecdf9fb`. The eight original files are preserved
byte-for-byte. The surrounding stacked branch is not part of this integration.

On 2026-09-21, WSL Python ran only `audit_replay.py` against a fresh extraction.
It returned `PASS_SELECTION_GATED_SAVED_MOVE_SCOPED_RAW_REPLAY`: all 62 manifest
hashes matched, both request/reply/action links and empty releases matched,
and SVG geometry was x=62/y=50/width=40/height=30 with no transform. The reviewer
also viewed the retained click-only PNG: the red rectangle has selection handles,
its status identifies a rectangle, and the toolbar shows X=50/Y=50/W=40/H=30.
No new GUI input or model call was issued.

Use the README's current replay instructions. The historical REPORT.md describes
`audit.py` as read-only, but that producer script invokes Docker and writes the
frozen audit JSON. Do not execute it against this preserved bundle. The portable
replay cannot independently establish historical container termination: those
fields remain producer attestations, and raw cleanup flags remain false.

This integrates a real-application evidence record for separating selection and
keyboard decisions. It adds no production mechanism, default delay, automatic
visual admission, or performance claim. The runtime already permits explicit
observation and bounded keyboard continuation; broader adoption still requires
transfer and matched benefit evidence.
