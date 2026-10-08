# A02 pre-freeze construction record

These checks are construction diagnostics only; none is counted as the formal A02 allocation. The H/T/D/C/U protocol was drafted before the full-matrix construction check, and the final protocol and executable sources were frozen only after fixing the diagnostics listed here.

- Host construction unit suite: 4/4 passed.
- Full construction rehearsal: 13 orders per principal, 23 reports, 169 truthful profiles, 7,774 candidate rows; independent oracle matched all rows and all four controls. It observed 7,178 report-dependent certificates and zero safe-beneficial deviations under the declared utility for both information partitions.
- Initial builder diagnostic: a profile vector was mistakenly passed as the complete order list to zip; fixed by selecting each profile's indexed orders.
- Initial audit diagnostic: no formal freeze existed yet; the auditor now permits freeze omission only when explicitly called as a construction tool. The formal runner always passes FREEZE_A02.json and the auditor checks its hashes.
- Initial identity diagnostic: the copied #6274 source had one extra trailing newline; the copy was corrected to the exact frozen source SHA-256.
- Initial oracle diagnostic: strict-pair list ordering was not canonical; it was normalized and the full-matrix construction check then passed.

The host rehearsal output is intentionally not part of the published evidence packet because it is pre-freeze construction, not a formal result. Its disposition is summarized here; the formal raw output and audit are retained separately.
