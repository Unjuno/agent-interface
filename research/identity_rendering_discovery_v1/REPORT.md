# Identity rendering discovery v1 — retained X11 evidence

## Decision

**HOLD for general same-target continuation.** The unchanged exact-pixel handle correctly rejects ambiguity, but its pixel evidence is neither rendering-invariant nor sufficient by itself to establish semantic target identity.

**RETAIN, conditional and narrow:** bind a target to an actually observed child-window XID when the backend can provide that identity. This used the existing scope check, not new runtime code. It rejects the tested destroy/recreate alias without breaking the tested stable or +6 px move cases. It does not fix benign rendering changes or establish applicability to browser/canvas subelements, reused XIDs, changed document context, or production input.

## Provenance and first outcomes

Immutable repository BASE: `b38e4e9734a1410aea8886900ed024ed04cca62b`.
Branch: `research/identity-rendering-b38e4e9`.
New-path scope only: `research/identity_rendering_discovery_v1/**`.
Related discussion: Issue #104; previous evidence PR #116 is unchanged.

The source copied through the GitHub connector was checked byte-for-byte using Git blob hashes before import. Direct container network downloads failed DNS resolution; no different implementation was silently substituted.

| Imported source | Git blob | SHA-256 |
|---|---|---|
| scoped_target_handle_v1.py | c4482bb7cd9c3a3e780c05bafa34073491a33ece | 550d377f145abbb16f8466dc91b5bb84ca25fccadf71e4d24b2f426550f5a19f |
| coordinate_frame_transform_v1.py | 972daffee40a38d3effbd8155f3da133d664e445 | cb6aefeaa4e9a41b4f4b9ca532e24106025247e39e7c7ee026ddc242a7cbb05b |

| Allocation | First disposition | Comparative trials | Change before successor |
|---|---|---:|---|
| identity-x11-scope-20260916-a1 | FAILED_SETUP: absent default Xauthority file | 0 | Private empty authority file for the cookie-less isolated display |
| identity-x11-scope-20260916-a2 | FAILED_SETUP: special non-window input-focus value | 0 | Explicitly focus only the private fixture root and synchronize |
| identity-x11-scope-20260916-a3 | COMPLETED; all mechanical checks pass | 120 pairs / 240 resolutions | None after the source freeze |

The allocation and source hashes were posted to Issue #104 before each attempt. a1/a2 sources, traces and logs remain in `evidence.tar.xz`; neither failure was relabelled or overwritten. The final runner SHA-256 is `9622b79584ceb7d24d9a458095f727bd1585033b5d04de862c6ad0d190d7b784`.

## Frozen experiment

One 320x200 RGB screen on Xvfb (24-bit depth), one native Tk button with a 10x10 deterministic icon, button bounds 32x24 px. Six cases, 20 repeated blocks, shuffled case order with seed 104316. The two arms receive the SAME source/current screenshots; their execution order alternates per trial. No threshold or detector tuning occurred after any scored result.

Cases: unchanged; same widget moved +6 px; real X11 pointer hover; one icon pixel's red channel increased by one code value; adjacent exact duplicate; destroy/recreate at the same position with identical pixels but a different fixture target.

Both arms import the actual `TargetHandleStore`, use radius 32 px, offset (16,12), TTL 30 s, freshness 5 s, and allow window/local translations. The `screen_chrome` frame is used as the API's absolute-screen coordinate path. Actual surface geometries are retained but do not supply a translation in this path.

The intervention is scope granularity: `top` binds the containing Tk top-level XID; `child` binds the child XID actually found at the originally declared center (112,92). The latter observation does not receive an oracle same-entity flag. It DOES receive additional backend identity information and therefore is not a screenshot-only method. The +6 px move keeps the original center inside the button; large-motion reacquisition is not tested.

The independent fixture scorer runs after resolution. It checks the original versus current XID, the XID under a returned point, actual rendering differences and duplicate/move pixel equality. It never provides logical target identity to the resolver. No button click or consequential OS input was issued. These are eligibility/identity tests, not execution/authority tests.

## Measured outcomes

Each table entry is a count among 20 repeated trials of the named, deterministic fixture condition. These are not 20 independently sampled applications or themes.

| Condition | Top-level scope | Child-XID scope | Interpretation |
|---|---|---|---|
| Stable | VALID 20/20 | VALID 20/20 | Original target point retained |
| Same target +6 px | REVALIDATED 20/20 | REVALIDATED 20/20 | Allowed local move retained |
| Hover, same enabled widget | MISSING 20/20 | MISSING 20/20 | Unnecessary refusal for this task; 668 changed pixels in the original box |
| One-pixel red-channel +1 | MISSING 20/20 | MISSING 20/20 | Unnecessary refusal; exactly one changed pixel was independently checked |
| Adjacent exact duplicate | AMBIGUOUS 20/20 | AMBIGUOUS 20/20 | Required ambiguity refusal retained |
| Identical-looking replacement | VALID 20/20; wrong logical identity eligible | SCOPE_MISMATCH 20/20 | Finer scope rejects this lifecycle alias |

All 120 trials pass the predeclared rendering/focus/geometry/lifecycle checks. The replacement screenshots are byte-identical to their source images while the fixture target XID changes. Under top-level binding the containing window and focus remain unchanged. Thus the top-level result is consistent with the advertised EXACT-PIXEL observational contract; it is not evidence that a production authority gate was bypassed.

The child's success on replacement does not repair hover or 1-LSB brittleness. These are two separate uncertainties and must not be collapsed into a single robustness claim.

## Actual timing, not nominal loop frequency

Conditions: Linux 6.18.44 x86_64, CPython 3.13.5, Pillow 12.3.0/XCB, Tk 8.6.16, Xlib module reports 0.15, Xvfb package 2:21.1.16-1.3+deb13u1. CPU reported INTEL XEON PLATINUM 8573C; 5 visible CPUs with affinity 0..4; /proc snapshot 2299.998 MHz. Clock frequency was not pinned and host contention is unobserved. Batch 1, one experimental session, no GPU. Audit used NumPy 2.3.5. Python package metadata for python-xlib was unavailable, so the module-reported version is recorded rather than inferred.

Timing uses `perf_counter_ns`, backed here by CLOCK_MONOTONIC, and separately records `process_time_ns`. The reported clock resolution is 1 ns; that is NOT a claim of 1 ns measurement accuracy. Resolver time brackets the resolver plus two process-clock reads, excluding capture, fixture mutation, PNG writing and independent scoring. Capture is timed separately. X-server CPU time is NOT included in the client process CPU counter.

| Condition | Top resolver median / empirical p95 (ms) | Child resolver median / empirical p95 (ms) |
|---|---:|---:|
| Stable | 26.718 / 35.763 | 27.144 / 33.390 |
| +6 px | 27.353 / 32.974 | 27.243 / 32.614 |
| Hover | 26.038 / 29.946 | 26.670 / 34.718 |
| One-pixel +1 | 27.855 / 33.133 | 27.423 / 37.516 |
| Duplicate | 28.738 / 33.696 | 27.246 / 35.994 |
| Replacement | 25.863 / 29.649 | 0.0232 / 0.0310 |

Across the 220 actual full-search calls, median 27.052 ms, observed range 23.206–42.861 ms. The 20 child-scope replacement refusals return before pixel search: median 0.0232 ms, range 0.0178–0.0316 ms. This is an early-refusal cost, NOT a matched task-completion speedup. Across 240 source/current captures: median 0.747 ms, range 0.293–4.627 ms. All raw integer endpoints are retained.

### Measurement variable/parameter table

| Symbol/name | Meaning | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| repetitions | Trials of each named fixture condition | 1 | 20 blocks | Fixed before scored execution; repeated known scene | Nonnegative integer scalar |
| radius | Bounded local exact-search margin | 1 (pixel count; physical scale unknown) | 32 image pixels horizontally/vertically | Same in both arms; not a distance in metres | Integer scalar |
| offset | Target point relative to the stored patch | 1 (pixel counts) | (16,12) | Inside the 32x24 patch | 2-vector of integers |
| capture0_ns, capture1_ns | Source/current capture start/end | s, stored as integer ns | Brackets only screen grab plus RGB conversion | Same monotonic clock; not true display scanout time | Pairs of integer timestamps |
| start_ns, end_ns | Resolver timing endpoints | s, stored as integer ns | Before/after the measured resolver section | Same process and monotonic clock | Integer scalar timestamps |
| cpu_ns | Client CPU consumed by measured section | s, stored as integer ns | Difference of process_time_ns reads | Excludes Xvfb CPU; not total system CPU utilization | Nonnegative integer scalar |
| XID | Observed X11 resource identifier | 1 | Top-level or child surface identity | Scoped here to one server lifetime; reuse not tested | Integer identifier |

Unit check: reported elapsed times subtract endpoints from the same ns clock and convert nanoseconds to milliseconds by division by 1,000,000. Pixel displacements remain image-coordinate counts, not physical lengths. No cross-clock latency is inferred.

## H / T / D / C / U

**H:** benign appearance changes can break exact-pixel continuity; coarse surface identity can admit an identical-looking replacement; finer observed identity may reject that replacement.

**T:** the frozen 120-pair Xvfb allocation above, retained after two zero-trial setup failures. First scored outcomes only; no favourable-sample selection or post-result runner changes.

**D:** bounded child-scope replacement check PASS: 0/20 replacement eligibilities; 20/20 stable and 20/20 moved-target acceptances; duplicate refusal unchanged. Broad rendering-invariant same-target claim FAIL on hover and one-LSB cases. General continuation/production promotion HOLD. Missing hashes/timestamps or mechanical inconsistencies would invalidate a claim rather than become zeros.

**C:** better scope information, not a better visual algorithm, explains replacement rejection. The two branches use exactly the same matcher and screenshots. Matching bytes does not certify business meaning, and a child XID can remain unchanged while its role or document context changes.

**U:** fixed known scenes, only five unique frame pairs, small repeated samples, CPU scheduling/host contention, non-atomic metadata/capture, synthetic observation adapter, XID reuse and canvas-only elements. The scorer establishes local widget lifecycle/point consistency, not user-intent semantics. No model latency, network, physical compositor, gameplay, lease/renewal, key release, input authority, or end-to-end task performance was measured. Combined uncertainty u_c and coverage factor k were not estimated; empirical ranges are reported instead of fabricated confidence bounds.

## Error check / independent audit

`audit.py` does not import or call TargetHandleStore. It uses NumPy array equality to independently enumerate each retained patch's matches and checks returned status, eligibility, point, scope, authority disclaimer and timestamp order. Result: **240/240 receipts checked; 120/120 trial mechanics checked; 12/12 run-manifest files verified; five unique retained frame pairs**. This is independent implementation checking on the same evidence, not a new live experiment.

The original a1 and a2 manifests were also recomputed successfully. A Pillow getdata deprecation warning is retained in stderr; it did not invalidate the run and the frozen source was not silently updated. A later optional distribution-metadata lookup failed for python-xlib; module version inspection is recorded separately in extra_environment.json.

## Reproduction / retention

The archive retains all three exact runner versions, imported source snapshots, every allocation freeze, setup failures, logs, full raw JSONL, five full-screen PNGs, schedule, environment, all integer endpoints, per-file manifests and independent audit result. No font files are included.

Unpack the archive into a fresh directory. Offline verification, with Pillow and NumPy available:

```bash
python identity_discovery/audit.py identity_discovery/third_run
```

The benchmark runner itself requires the pinned source files, Tk, Xlib, Pillow XCB and Xvfb. A NEW live replication must have a NEW allocation label and fresh output directory; freeze the new source hash before running. Do not rerun the consumed a1/a2/a3 identifiers or overwrite their outputs. Offline audit is sufficient to regenerate the correctness findings; historical timing values come from the retained timestamps, not a promised identical-speed rerun.

## Smallest successor, not an automatic new feature

Test a same-XID, same-pixel control whose application/document meaning changes. This separates lifecycle identity from semantic dependency validity. Do not add fuzzy matching, a new tracker, or a high-frequency full search merely because exact matching refuses hover. The next mechanism should be selected from that counterexample, not from a preferred architecture.
