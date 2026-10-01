# Publication review notes (postformal, not a revised scientific freeze)

The uploaded source files and audit summary are exact copies. The full conversation archive contains all 196 original files, including its manifest, and was extracted and re-audited with byte-identical AUDIT.json. ARCHIVE_REAUDIT.json records that separate process. No formal case was repeated.

Delivery is incomplete: this GitHub tree does not include formal-01 or the frozen construction inputs. A repository-only audit cannot run until the complete original archive is durably published. Keep the PR Draft; do not merge or close Issue #3985. PUBLICATION.json records the missing-artifact identity, not an accessible GitHub attachment. Source/summary publication is not raw-evidence publication.

The reader's existing default is max_records=32. This experiment compares explicit page1/page8/page32 settings; it does not introduce a new faster reader or establish an improvement over the existing default. The page1 control is not represented as the default Agent Interface baseline.

The timed plain drain excludes delegating byte/hash counters, file creation/priming, JSON serialization and subprocess startup. It includes Python loop/cursor handling, per-call clock sampling and in-memory response retention, not just pure read_pending CPU instructions. Therefore the measured wall ratio is for this complete local drain harness. The independently derived logical-byte law does not apportion that wall ratio among hashing, decoding, allocation and loop overhead.

Only the additive research namespace is changed. No production API/default/queue, global roadmap, predecessor or parallel branch is modified. A future live producer/model comparison must account for notification latency, already-available backlog, total retained log size and model-visible endpoints separately.
