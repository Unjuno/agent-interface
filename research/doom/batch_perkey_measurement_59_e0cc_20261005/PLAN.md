# #59 batch-compatible per-key measurement integration, ordinary regression work

Worker: root session root-e0cc, FINAL-v5.
Branch: fix/59-perkey-owner-guard-e0cc-20261005, extending own draft #8094.
Basis: #8065 6591b5703862c73d375a6646374ad82a26505bcb + own #8094 guard + cherry-picked #8103 batch sample custody fix (3449e358a872b791fd94dff34edf24dc6e4298c2). Combined local base 935473ee53.
Resources: private local Python process and fake Xlib only; existing bugbot slot for independent inspection. No native X, GUI, game, model, container, formal allocation, main update.

H: Opt-in measurement on the current raw owner can pair per-hold DOWN and ordered batched UP keymap observation brackets while preserving batch query placement, retries and release-pending. V15 can select this explicit compatible backend and accurately pin its source. Scope is conservative server-keymap sampling, not application consumption, physical dwell, live timing or task effect.
T: Fresh-process startup before Session; real owner thread with fake Xlib normal/repeated/duplicate holds, first/last retry, pre/post errors, persistent loss, cleanup identity and cancel/focus/expiry during added DOWN pre-sample; V4/backend/projector composition. Reuse existing source-custody and cancellation regression entry points. One red and green ordinary regression cycle, repair only concrete failures while retaining every result. Separate-agent raw/code audit and targeted independent checks after author tests.
D: PASS only if source selection is correct; timestamps come from actual sample start/end; same owner/token/key/actuation ties one down/up; no extra query between original batch UPs; failed/missing/ambiguous samples and incomplete batches do not claim confirmed intervals; later DOWN remains blocked after unknown release; default disabled owner retains existing query contract. Unknown or unexercised live behavior remains unverified.
C: Imported archived owner has no up_batch; forcing it is not a solution. Backend-call times do not bound physical edges. Shared batch samples are correlated, not independent observations. Global keymap cannot prove application consumption or exclusive physical authority. Failed DOWN / duplicate DOWN / cleanup must not leave a pairable stale identity.
U: Fake keymap and synthetic timestamps do not establish real latency, scheduler bounds, X server interoperability or game outcome. No nonauthor integration quorum assigned; technical audit is not a merge vote.

Construction note: initial sparse-checkout add used an unsupported --no-cone option; no test/runtime was executed. Following already-authorized parent evidence merge completed. Corrected sparse add and #8103 cherry-pick then succeeded. Original tool output remains session evidence.
