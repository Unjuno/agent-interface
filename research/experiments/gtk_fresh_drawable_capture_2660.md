GTK fresh drawable capture preflight (#2660)

H/T/D/C/U

- Hypothesis: capturing each fresh GTK window's own X drawable preserves case identity that is lost by capturing the Xvfb root.
- Test: local Docker image codex-gtk-model:local (GTK3 + Xvfb); eight fresh windows; Xlib drawable capture; SHA-256 observation identity; independent disposition scorer.
- Data: useful, unavailable, guarded, no_effect, partial, stale_repair, ambiguous, cleanup_failure.
- Control: no model calls; replay_allowed=false; unsafe delivery/cleanup cases yield.
- Variables: fresh window, case color/geometry, drawable dimensions, observation hash.

Result

- 8/8 cases present.
- 8/8 distinct drawable observation hashes.
- Dispositions: SUCCESS, YIELD, YIELD, NONE, PARTIAL, YIELD, YIELD, YIELD.
- Root-capture negative control: 3 distinct hashes/8.
- Local fixture/preflight only; not formal #2606 acceptance and not production adapter integration.

Reproduction used work/gtk_eight_case_drawable_capture.py with codex-gtk-model:local, GTK3, Xvfb, and /usr/bin/python3. Next step: replace synthetic scorer inputs with real adapter/effect/cleanup receipts required by #2606.