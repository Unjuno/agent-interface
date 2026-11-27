# Frozen method

## H/T/D/C/U

**H:** On the 21 fixed archived 1280x800 RGB observations listed in `design.json`, at least one exact focused crop produces a strictly smaller canonical JSON+base64 payload than the full-frame encoding made by main's `ImageArtifactSink` under the same frozen Pillow environment.

**T:** Use `research/observation_tiles/image_artifact.py` unchanged at `compress_level=6`. Decode each pinned existing observation PNG, verify its exact pixel digest against the retained `observations.jsonl`, then encode one full-frame artifact and crop artifacts for four exact pixel-area sizes (1/16, 1/4, 1/2, 3/4) at center and four corners. Add one full-bounds crop control per frame. This yields 420 size/placement cases plus 21 no-gain controls = 441 cases. Compare canonical sorted compact UTF-8 JSON bytes containing base64 PNG and frame/epoch/codec/region/bounds/reason metadata. Select focused only when its complete JSON is strictly smaller; otherwise select FULL_FRAME.

**D:** `PASS_METHOD_SCOPED` requires 21/21 source frames to match their ledger pixel digests; exact reconstruction of all full and crop PNGs; 441/441 rows and canonical byte counts; all preregistered corruption/schema/identity/size mutations rejected; strict-savings-only selection; all 21 full-bounds controls falling back; and at least one positive saving. If reconstruction/audit integrity fails, retain FAIL/STOP as specified and do not rerun. If exact audit passes but no valid crop saves bytes, disposition is `HOLD_NO_SIZE_GAIN`.

**C:** Existing #1935 request-validation evidence covers deterministic freshness/identity/focus/bounds checks; A02 covers synthetic gray8 byte accounting; A03 preserves the distinct synthetic stdlib-PNG allocation as `HOLD_RUNNER_EXIT_UNCAPTURED`. This A04 uses a different encoder and retained GUI frames. These results are not pooled.

**U:** Fixed finite screenshots and this Pillow version only. ROI semantic quality, excluded context, model/token utility, wire/network bytes, encode latency, live GUI, action authority, task effect, human tempo, and product success remain untested.

## Custody and one-shot rule

Before execution, freeze the exact base, `ImageArtifactSink` source, Pillow/runtime identity, all four observation ledgers, all 21 referenced PNG byte hashes and pixel hashes, code, cases, commands, gates, and outputs. Attempt read-only OrbStack image inventory. If unavailable, run once under macOS network-deny sandbox using the pre-existing bundled Python/Pillow; explicitly report host-only evidence. The candidate is invoked exactly once. Invoke the independent raw-only auditor exactly once only after candidate exit 0 and complete raw output are confirmed. Preserve first outcomes, including infrastructure or custody HOLD; retries are zero. Never rerun this allocation.

The candidate creates PNG files via the frozen main `ImageArtifactSink` source and emits one raw JSON record with artifact paths, hashes, sizes, decisions, and counts. The auditor independently verifies PNG chunk CRCs, zlib streams, PNG filters, exact input/crop RGB bytes, metadata, serialization lengths, all cases, and mutation controls without importing candidate code or Pillow.
