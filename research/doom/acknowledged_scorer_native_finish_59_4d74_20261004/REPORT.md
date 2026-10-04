# Native external finish composition

Exact source: 603f7b70e66a3866c11684dc8c869f12479ce08d. Prospective protocol: PR7545 comment5978075816. One WSLc cached CPU-only/no-network/nonroot native ViZDoom1.3.0 ASYNC_SPECTATOR run; seed40109, Freedoom MAP01, timeout350 tics. No available buttons or positive input. Frozen argv, image, WAD and source hashes are in out/FREEZE.json; original bytes are preserved.

PASS_NATIVE_EXTERNAL_FINISH_COMPOSITION_SCOPED; exit0. Initial update tic3→5; after12s passive wait, external update5→426. Final sample consumed that acknowledgment without another update (2 before/after close). Actual sink:2 samples,1 negative EPISODE_FINISHED_NO_EXIT,0 useful-positive events. Engine not running after close/cleanup. No retry/replay.

This exercises actual AcknowledgedSampler, ObservedGameProxy, unchanged V15 sampling helper and ScorerFileSink together. It does not run full V16 main, X11/controller/model/GPU, positive gameplay, reset/epoch transitions, independently trusted score-field freshness, controller neutrality or cadence bounds. Requested CPU/memory limits are not demonstrated enforcement. Run/update identifiers are client provenance. Earlier results remain unchanged; roadmap59/57 remains incomplete.
