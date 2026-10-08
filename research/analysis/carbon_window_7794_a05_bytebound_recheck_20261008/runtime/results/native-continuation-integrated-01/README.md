# Native continuation and finish integration: one WSL live trial

The primary assistant used source `0548066ebda3e56bb84442d792699426350d5ef9`
through the repository's sequential MCP relay, one persistent SDK connection,
one fresh Inkscape allocation, seed 991123 and a two-stage bound. The relay's
stdout was redirected directly to JSONL before terminal rendering. Three MCP
image blocks were forwarded to the assistant; full responses are retained.

After viewing the initial rectangle, the assistant clicked it and issued six
Right chords. The returned image showed X=62, Y=50, width=40, height=30. Its
continuation reported stage 2 / source sequence 7 with the next source hash.
The assistant consumed that stage and sequence, issued six more Right chords
and Save with finish_after. The final image and independently parsed saved SVG
show X=74 with the other geometry preserved: the public goal's dx=24.

The final reply reports action completed, feedback matched, evaluation success
and cleanup completed. No third source was published. A separate native_status
call observed owner PID 19391 terminal with exit 0; the relay then exited 0 on
EOF. Cleanup records preserve child return codes 0, 1 and -15, rather than
claiming every child exited successfully. native_status does not itself verify
task success or cleanup; those claims come from the final reply and saved file.

This is a new successful combined-source trial, not a reinterpretation of the
failed `native-continuation-live-01` trial. It differs from that trial and
`native-finish-restored-01` in the final movement count (six rather than twelve),
so it is not an identical-action performance comparison. No recovery or
additional observation request was needed in this one trial. This does not
establish a reliability rate or fewer roundtrips against a controlled baseline.

Run `python audit.py` here to check retained byte hashes, image identity,
continuation/request linkage, releases, geometry and terminal status. The audit
is a programmatic check authored by the same assistant, not an external review.
The manifest covers all retained files except itself. SDK intervals are local
timing descriptions; host presentation, model-visible delivery, model usage,
cost and human comparison remain unmeasured. Docker was not restarted or used;
the real-container gate in issue #3352 remains unmet.
