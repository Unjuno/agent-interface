# #1325 preformal stack-localized stop

Disposition: `PREFORMAL_SETUP_STOP_TEMPORAL_OCCUPANCY_NS_EXPANSION`; scientific disposition **NONE**.

- construction2 / formal0 / reruns0
- control complete/clean
- V12_EFFECT child timed out at8s; durable faulthandler stack captured successfully
- stack localizes the main thread to #988 `candidate.py:51 occupancy_only`, called from `analyze`
- #988 v1 computes integer union lengths by materializing `set(range(wait.lo, wait.hi))`
- live timestamps are `perf_counter_ns`; a 150 ms hold implies roughly 150 million integer points before set intersections
- no physical/effect scientific row is reconstructed from the killed child
- cleanup residual0

Next step is offline-only: implement a versioned interval-union occupancy algorithm that is mathematically equivalent to #988 v1 on bounded integer domains, then separately test ns-scale inputs. Do not edit #988 retained first outcome or rescue #1325 in place.
