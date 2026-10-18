# A01 run record — retrieval surface STOP

Allocation: `RELATION-FIRST-8073-REAL-CORPUS-A01-20261007-01`
Protocol: `PROTOCOL.md` (frozen before the call)
Frozen base: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`
Disposition: `STOP_SEARCH_SURFACE_BUDGET_NONCOMPLIANT`
Hypothesis decision: **UNEVALUATED**

## One-shot request

On 2026-10-07, one web-search request submitted the four frozen queries for targets #8166 and #7831 together, with `response_length="long"`. There was one keyword-first and one relation-first query for each target; no query was submitted again. The exact query text is frozen in `PROTOCOL.md`.

The search tool returned 27 displayed results in one combined response. This exceeds the protocol's maximum of five results per query (20 total for four queries), and the combined rendering did not carry a reliable query-to-result partition. Results also mixed scholarly records, a Q&A post, general web pages, and non-primary summaries. Consequently:

- candidate lineage and equal per-query result caps cannot be audited;
- no stable/frozen source-corpus snapshot was established;
- target pairs for #7802, #7794, #8057, #5368, #6524, and #7165 were not run;
- no result was deduplicated, excluded, rated, or treated as a scientific candidate;
- no assessor packet, panel rating, candidate script, auditor, or formal analysis was run.

This is a search-surface/protocol execution STOP, not evidence for or against relation-first retrieval. The four submitted queries are consumed in A01 and will not be retried or replaced. A corrected search method requires a separately preregistered allocation with a fixed, versioned corpus and a response mechanism that enforces and preserves per-query limits and lineage.

## Preserved visible response inventory

The following entries were visible in the combined tool response. Because the tool omitted reliable per-query grouping, this is an inventory only; it does not assert which query retrieved any item or that the page is a valid source.

| Ref | Displayed result | URL |
|---|---|---|
| 0 | How can screen reader users resume reading after closing a modal window? | https://stackoverflow.com/q/79759542 |
| 1 | Dynamic management of periodicity between measurements in predictive maintenance | https://doi.org/10.1016/j.measurement.2023.112721 |
| 2 | A myopic policy for optimal inspection scheduling for condition based maintenance | https://www.sciencedirect.com/science/article/pii/S0951832015001842 |
| 3 | Optimal Scheduling of Fallible Inspections | https://ideas.repec.org/a/inm/oropre/v44y1996i2p360-367.html |
| 4 | Analysis of a 2-phase model for optimization of condition-monitoring intervals | https://www.researchgate.net/publication/3152066_Analysis_of_a_2-phase_model_for_optimization_of_condition-monitoring_intervals |
| 5 | The Inspection That Stopped Recurring | https://awraops.com/blog/the-inspection-that-stopped-recurring |
| 6 | Recurring Inspection | https://abstractopedia.org/mechanisms/recurring_inspection/ |
| 7 | After barge-in, keep the playback position | https://hci.top/en/handbook/M3.04.2 |
| 8 | A Dynamic Methodology for Setting Up Inspection Time Intervals in Conditional Preventive Maintenance | https://www.mdpi.com/2076-3417/11/18/8715 |
| 9 | Risk-Based Inspection Schedule | https://abstractopedia.org/mechanisms/risk_based_inspection_schedule/ |
| 10 | Navigation State Restoration | https://nalu-development.github.io/nalu/navigation-restore.html |
| 11 | Failure Detection Window in Oil Analysis | https://shop.oil-testing.com/failure-detection-window-in-oil-analysis/ |
| 12 | A Safety Constrained Control Framework for UAVs in GPS Denied Environment | https://arxiv.org/abs/1910.10826 |
| 13 | Safety Constrained Multi-UAV Time Coordination | https://arxiv.org/abs/2005.07697 |
| 14 | Safety-Critical Control for Systems with Impulsive Actuators and Dwell Time Constraints | https://arxiv.org/abs/2303.10243 |
| 15 | Dynamic Control for Random Access in Deadline-Constrained Broadcasting | https://arxiv.org/abs/2108.03176 |
| 16 | Federal Register, Vol. 75, No. 85 | https://www.govinfo.gov/content/pkg/FR-2010-05-04/pdf/2010-10105.pdf |
| 17 | Safety Reports Series | https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1473_web.pdf |
| 18 | Managing integration of pre-closure | https://www.iaea.org/sites/default/files/19/02/geosaf-2-tecdoc-draft.pdf |
| 19 | 21.12 Condition Monitoring | https://www.cur.ac.rw/mis/main/library/documents/book_file/2015_Book_PhysicalAssetManagement.pdf |
| 20 | Predictive maintenance | https://en.wikipedia.org/wiki/Predictive_maintenance |
| 21 | Cascade chart (NDI interval reliability) | https://en.wikipedia.org/wiki/Cascade_chart_%28NDI_interval_reliability%29 |
| 22 | Condition monitoring | https://en.wikipedia.org/wiki/Condition_monitoring |
| 23 | UNIVERSITY OF CALIFORNIA, | https://escholarship.org/content/qt9w86q269/qt9w86q269_noSplash_a8fa753e10a2a3a281d420c7cac1edcc.pdf |
| 24 | Can cursor please stop this auto scrolling so I can read what the agent thinks? | https://www.reddit.com/r/cursor/comments/1sma501/can_i_stop_this_auto_scrolling_so_i_can_read/ |
| 25 | Read the entire view or read from current position to the end | https://ptacts.uspto.gov/ptacts/public-informations/petitions/1524828/download-documents?artifactId=-QTaBxqYbBKXEwONslnVY1S8xXbWiRxrgrFM8dYiwmqgg-Dl_QIrWMw |
| 26 | Condition monitoring | https://en.wikipedia.org/wiki/Condition_monitoring |

The inventory is transcribed from the search tool's rendered response, not a byte-for-byte API payload. The original rendered response remains in the task's tool transcript; no claim of lossless raw-response archival is made.
