# Constructor-close-fault saved evidence rescue

Original PR #7052, exact source `fdfd71623756eba4899cf9c14bcb162e4a60c755`.
All 45 original packet files are restored unchanged, including unused first
freeze/extra-LF source transport incident and original raw/receipts/journals.

Fresh read-only validation checks the manifest and invokes only the completely
reviewed original oracle's pure `check(rows)` function selected through AST.
Top-level collector/oracle execution, PID stamping and AUDIT output writes are
suppressed; no injected native experiment, child process or allocation rerun.
This checks saved-row consistency, not native authenticity/new fault observations.

Original cooperative fault construction separates preserving primary exception
identity from actually releasing a journal. Diagnostic notes do not prove release;
pre-close injected failures can leave the file open until labelled driver cleanup.
Historical cleanup is not current FD/PID absence. No hostile close/add_note hang,
partial process acquisition, task/model/GUI/recovery efficiency is certified.
Original #7018 evidence and votes remain unchanged. No production patch applied.

Local CI, review and main integration are pending. Source ref remains preserved.
