# Allocation 02 construction history

Scientific formal rows remain **0/12** in every construction run. No construction run emitted task input.

1. Run `35821558853`, head `e53df6d6aecdb1e6e1f8880228079ca66352e954`: **construction FAIL** after exact bridge observation, before any input. The selected mint patch was visually flat and canonical `FlatTargetRefused` rejected it. Artifact `10733837008`, SHA-256 `2430b3d4200d9a1ff0a913a1831bf087b89a8a42e2ae81679e53142badaa1f83`. The flat-region guard was not relaxed.
2. Run `35821713612`, head `9b011b094de6e3201e3783797ba87500a06a6744`: PASS after moving only the construction point to an existing non-flat stripe boundary.
3. Final exact-source run `35821932965`, head `a94632a2dd4a40042f4914de4cf498c1f1b89407`: **PASS_CONSTRUCTION_EXACT_BRIDGE_TOPOLOGY** after adding the read-only effect observer method used by formal. Artifact `10733034046`, SHA-256 `cbf2b27b672fa0a905343ea97fd0c91aa76eafa3d41d82c8b4803bf0d48fffc8`.

Final construction facts: same-client XID `4194304 -> 4194304`; two 123,200-byte client-window pixel buffers with identical SHA-256 `04b657f39f16ef15d13c2566464d2bdd5d21ead9cd2549ac7f422474124726ba`; exact DestroyNotify; canonical NativeHandleBridge observation + non-flat mint; `review_window` status reviewed and binding revision 1; old alias MISSING; fresh mint succeeds; backend emissions 0; recovery_required false; Openbox/Xvfb clean and socket absent.

The two base64 ZIPs beside this note retain the first failed construction and final passing construction exactly. The intermediate PASS remains identified by Actions run/head and is not pooled into formal data.
