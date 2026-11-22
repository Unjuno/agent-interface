# Active-turn observation ID boundary A02

## H / T / D / C / U

- **H:** A corrected App Server probe that compares the actual `ExternalMessage` response turn ID with the original active turn can verify or reject same-turn acceptance, while confirming the message image in the next mocked Responses request.
- **T:** On Codex CLI 0.160.0, send one `ExternalMessage` while the first loopback-mock Responses request is held. Run once with `detail=auto` and once with the preregistered `detail=low` negative control. Extract the ID from the external RPC response; do not infer it from request context.
- **D:** `AUTO_PASS` requires accepted external response, actual returned ID equal to the original active ID, exact observation text and frame bytes in request 2, and a completed turn. `LOW_IMAGE_OMITTED` is expected only if the RPC identity/text control passes but request 2 lacks the image. Any other outcome is retained as failure/STOP.
- **C:** The model endpoint is a loopback mock and performs no inference; the test exercises local App Server protocol and request serialization only.
- **U:** No model comprehension, policy change, actuator stop/release, V39 runtime wiring, useful feedback, recovery, or live-game outcome is established. This does not satisfy #59's fresh live threat exposure; no live lane is implied.

## Relation to A01

A01's first raw protocol output is preserved. Its `same_turn_id` assertion compared the initial ID with itself, so its transport evidence remains useful but its active-turn identity claim is unverified. A02 corrects that check and adds a mismatched-ID control; it does not rewrite A01's result.

## A02 result

Both preregistered one-shot controls completed on Codex CLI 0.160.0. The actual external `turn/start` response contained a turn ID equal to the original in-progress turn ID in each run, and each run completed with two loopback Responses requests and no server errors.

- **AUTO_PASS:** exact text and the 149,687-byte retained PNG (SHA-256 `0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c`) were present in request 2; `input_image_count=1`; exit 0.
- **LOW_IMAGE_OMITTED:** exact text and same-turn identity passed, while request 2 had no image (`input_image_count=0`); exit 1, as preregistered for this negative control.

Raw stdout is preserved in `auto.json` and `low.json`. The assertions are checked with five unit tests, including a mismatched-ID rejection. This establishes only local App Server external-message transport and serialization against a loopback mock. It does not establish a model response to observation, live policy change, immediate stop/release, V39 runtime integration, or the fresh live threat exposure required by #59.
