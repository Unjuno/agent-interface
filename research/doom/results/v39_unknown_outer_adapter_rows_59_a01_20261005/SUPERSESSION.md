# Supersession note — 2026-10-05

After this branch's A01 baseline/candidate regression run, the latest open draft #7690 had advanced from the parent snapshot used here (`73ccfa7696c1b005be7c1c59e63d1c06dfe3674d`) to `aa88a9d95e208d413e64a23fe30754ec52c9ad55`. That newer head adds unknown and legacy outer-event handling and corresponding regression cases, in addition to further nested-identity protections. It supersedes the production change on this branch, so no duplicate PR was opened.

This branch's three-case run remains its own historical scoped result. Its independent auditor stopped at A05 because a mutation control did not validate the expected frozen source hash; it is not an independent-audit PASS and does not replace the evidence retained in #7690. The branch was pushed for recoverability and is not proposed for merge.
