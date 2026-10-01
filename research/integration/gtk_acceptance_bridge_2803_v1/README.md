# Acceptance bridge for retained GTK matrix evidence (#2803)

This path independently audits the retained Docker result from #2796/PR
#2801. It does not rerun the experiment or reinterpret the result. The bridge
checks case order, expected dispositions, authority/release receipts,
independent effects, stale/ambiguous no-replay, terminal cleanup failure, and
the retained source/image identity metadata.

The retained image is
`sha256:8e249b9ab9761d1c14fada1eca727b55564f70d67b0f06ae9e9854682fd60199`.
The result remains scoped: `PASS_ACCEPTANCE_BRIDGE_SCOPED` is not a claim of
model utility, human tempo, cross-platform support, or product readiness.
