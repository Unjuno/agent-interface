# Native GUI multi-seed evaluation

The provenance-verified 120-frame clutter/occlusion dataset was trained and evaluated five times with independent deterministic split/model seeds using the same 354-parameter CUDA CNN.

Results: seed 2203 1.000/0 FP; 2204 1.000/0; 2205 1.000/0; 2206 1.000/0; 2207 0.975/0. Mean accuracy 0.995; minimum 0.975; aggregate false positives 0.

This supports repeatability within the bounded controlled-GUI fixture only. The minimum run is the conservative boundary; no universal reliability or gameplay transfer claim.
