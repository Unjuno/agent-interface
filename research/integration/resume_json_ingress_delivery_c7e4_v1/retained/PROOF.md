# Information-loss boundary (analytic prerequisite)

## Variables
| Symbol | 日本語での意味 | SI unit | Definition | Domain / premise | Type |
|---|---|---|---|---|---|
| b_good | 重複なしの有効JSON | 1 (byte-count representation) | one task_active=true member | finite UTF-8 bytes | byte vector |
| b_dup | 重複ありのJSON | 1 | task_active=false followed by task_active=true | same other fields | byte vector |
| P | 通常JSON復号 | 1 | keep last duplicate member | deterministic decoder | function |
| V | 変換後の判定 | 1 | sees only decoded mapping | no raw/provenance side channel | function |
| A | 復帰許可ラベル | 1 | RESUME eligibility, no input authority | discrete label | scalar label |

By last-member retention, P(b_good)=P(b_dup). For any deterministic mapping-only V,
substitution gives V(P(b_good))=V(P(b_dup)). If valid stable b_good must be eligible A,
then b_dup receives A too. Therefore such V cannot both preserve that positive and reject
this duplicate without an additional pre-decoding witness. Rejecting both is possible but
loses the required positive; this is not an impossibility of conservative abstention.
The raw strict entry checks pairs before dictionary collapse and can distinguish the two.

This is a representation result, not authentication. An intact but false Boolean true
looks identical to an honest true to all three candidates. A trusted current producer or
an independent source-bound current check is necessary to distinguish those worlds.

Unit check: bytes, Boolean values and eligibility labels are dimensionless discrete
objects. No equality here compares seconds with counts. Runtime nanoseconds are stored
integer time readings (1 ns=10^-9 s) and used only within the same monotonic clock domain.

ERROR CHECK: preservation of the valid positive is an explicit premise; no inference is
made from syntax to reality, absence of a duplicate to authenticity, or eligible to authority.
