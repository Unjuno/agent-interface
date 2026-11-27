# Preregistration: current-main Calc same-frame Save integration, r84-c8

Date: 2026-11-03. One local Docker/Xvfb task attempt; no model or provider.
Source is frozen at current `main` `cf3ddf2f8ef44f78fac3cfed78df2904aa596691`.

## Question and hypothesis

Does the merged same-frame effect-verifier path retain the registered Calc
Save-request receipt when the post-Save frame digest is unchanged, and can the
separate parent verifier still prove the exact saved task after verified input
release and natural application exit?

H: a fresh `calc-ocr-save-v1` task will record an unchanged digest across the
Save effect observation, emit `effect_checked(status=unavailable)` rather than
`no_progress`, bind exactly one `calc-task-save-request-v1` to the attempt and
target generations, preserve the exact A1=731/A2=864 saved FODS, release both
input transitions, and close with clean natural Calc/oosplash exit.

## Frozen conditions and one-shot rule

- Unique attempt ID: `issue57-r84-c8`; one fresh Calc generation and one
  disposable container. No retry, replacement, silent exclusion, or replay of
  r73–r83. Any setup, task, cleanup, or verification failure remains the result
  of this one attempt.
- Current source: `cf3ddf2f8ef44f78fac3cfed78df2904aa596691`; exact source
  hashes are in `source-freeze.json`. Fixed existing image ID
  `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`.
- Docker limits: 2 CPU, 4 GiB memory and swap total, 256 PIDs. Read-only source
  mount; only this attempt directory is writable. The script installs the exact
  LibreOffice and Tesseract package versions from the existing r78–r83 runner;
  that package setup needs the configured Debian mirrors. The script makes no
  provider/model/API calls. No image pull, build, prune, Docker setting change,
  WSLc allocation, or MAP01 run.
- Xvfb `:97`, 1280x800x24, fresh task-owned blank FODS, fixed entry/save/exit
  coordinates and fixed profile. Only `OCR_GUARD_CONTROL=skip`; this is a
  functional seam check, not a comparison or efficiency estimate.
- The container's task execution is bounded by 600 seconds. Preparation and
  apt logs are retained. Docker must respond and the attempt container must exit
  before any subsequent work.

## Pass rule

PASS only if all gates hold in this attempt:

1. The compiled receipt contains the exact `enter` then `save` two-transition
   sequence; both transition releases are verified.
2. The last two accepted observations have equal evidence digests. The Save
   effect has a correlated `effect_checked(status=unavailable)` event and
   verification timing; it does not terminate as `no_progress`.
3. Exactly one server-owned Save-request receipt exists, with schema
   `agent-interface/calc-task-save-request-v1`, attempt/call/target-generation
   joins matching the task artifact descriptor and saved controller receipt.
4. Independent pre-close parsing and the after-close parent verifier both
   report exactly A1=731 and A2=864, verified task success, and the same
   artifact SHA-256.
5. `interface_close` confirms empty keys/buttons, verified release, and owner
   exit 0. The exact Calc target and oosplash launcher each naturally exit 0;
   clean process-group exit is verified; parent task verification succeeds.
6. Docker container exit is 0 and Docker Engine remains responsive afterward.

Any missing or contradictory evidence is FAIL/UNKNOWN, never PASS. No speed,
token, price, or cross-domain inference will be calculated from this single
attempt.

## Evidence and interpretation limits

Keep full raw JSON, FODS bytes, OCR/image artifacts, setup and container logs,
exit code, source freeze, conditions, audit output and hashes in this directory.
This only tests one scripted local LibreOffice Calc task. It cannot prove live
provider behavior, model accounting, general reliability, WSLc, MAP01, or
Issue #57 completion.
