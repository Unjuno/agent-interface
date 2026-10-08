# A03 first outcome

Classification: `REPRODUCED_WITH_POST-OBSERVATION-STOP`.

The frozen schedule was observed: the owner thread sampled cancellation false at `100780455030583 ns`; the `up` request was dequeued at `100780455057041 ns`; cancellation was set at `100780455057500 ns`; owner `KeyRelease` began at `100780455061125 ns` and the fake side effect was recorded at `100780455062666 ns`. At request time, the wrapper recorded `cancel_requested_at_request=false`, `ordinary_release_candidate=true`, and `owner_thread_keyup_verified=true`. The later cancellation cleanup record verifies an empty fake keymap.

The candidate exited 1 after the target event, when its ancillary `input_state` observation accessed `root_x` on an incomplete fake pointer object. The frozen audit v1 is retained as failed: it requires candidate exit 0 and a successful post-up state query. Audit v2 independently applies the frozen hypothesis gate and passes four negative controls; it reports the target boundary as reproduced while preserving the overall post-observation STOP. No candidate retry occurred.

Interpretation: the `ordinary_release_candidate` field reflects cancellation state when the caller requested up, while the owner-side key-up occurred after cancellation became set. This exposes a measurement boundary in the synthetic schedule; it does not show an unsafe release, estimate race frequency, or establish an X server, game, physical input, application effect, or live recovery behavior.
