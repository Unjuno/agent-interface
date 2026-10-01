"""One bounded rephasing step from full acquisition duration, never from game score."""
import os
from schedule import offsets_ns

def correction_ns(duration_ns):
    if type(duration_ns) is not int or duration_ns < 0:raise ValueError('invalid duration')
    return min(20_000_000, max(0,duration_ns-1_000_000_000//140)) if duration_ns > 1_000_000_000//70 else 0

def make_stdin(base_class, stream, sample_fn, sink, mode, count=30, loop=None):
    """Keep the retained fd parser and main-thread dispatch; replace timing only.

    A late invocation takes one current sample at the latest elapsed slot and
    records skipped slots. It never manufactures catch-up samples. All arms have
    one common calibration sample then the declared finite scheduled requests.
    """
    class PhaseStdin(base_class):
        def __init__(self):
            super().__init__(stream, sample_fn, sink, sample_hz=10., loop=loop)
            if mode not in ('static','rephase'):raise ValueError('unknown mode')
            self.offsets = offsets_ns('late', count)
            self.bootstrap = int(os.environ.get('PHASE_BOOTSTRAP_NS','0'))
            if self.bootstrap not in (0,12_000_000):raise ValueError('unfrozen bootstrap')
            self.adjustment = 0
            self.anchor_ns = None
            self.next_index = 0
        def _sample_due(self):
            now = self.loop.clock_ns()
            skipped = 0
            if self.anchor_ns is None:
                scheduled, index = now, 0
            elif self.next_index >= len(self.offsets):
                self.next_sample_ns = now + 200_000_000
                return False
            else:
                scheduled = self.anchor_ns + self.bootstrap + self.adjustment + self.offsets[self.next_index]
                self.next_sample_ns = scheduled
                if now < scheduled:
                    return False
                while self.next_index+1 < len(self.offsets) and self.anchor_ns+self.bootstrap+self.adjustment+self.offsets[self.next_index+1] <= now:
                    self.next_index += 1
                    skipped += 1
                scheduled = self.anchor_ns + self.bootstrap + self.adjustment + self.offsets[self.next_index]
                index = self.next_index + 1
                self.next_index += 1
            started = self.loop.clock_ns()
            payload = self.sample_fn()
            finished = self.loop.clock_ns()
            if self.anchor_ns is None:
                self.anchor_ns = finished
            applied = self.adjustment
            if index == 1 and mode == 'rephase':
                self.adjustment = correction_ns(finished-started)
            self.sink(dict(scheduled_ns=scheduled, sample_started_ns=started,
                sample_finished_ns=finished, start_lateness_ns=started-scheduled,
                missed_periods_before=skipped, payload=payload,
                schedule_index=index, schedule_mode=mode, anchor_ns=self.anchor_ns,
                bootstrap_shift_ns=self.bootstrap, applied_adjustment_ns=applied, next_adjustment_ns=self.adjustment))
            self.samples += 1
            self.missed += skipped
            self.next_sample_ns = (self.anchor_ns + self.bootstrap + self.adjustment + self.offsets[self.next_index]
                if self.next_index < len(self.offsets) else finished+200_000_000)
            return True
        def stats(self):
            return dict(super().stats(), mode=mode, anchor_ns=self.anchor_ns,
                planned_scheduled_count=count, emitted_count=self.samples, bootstrap_shift_ns=self.bootstrap, final_adjustment_ns=self.adjustment,
                schedule_offsets_ns=list(self.offsets),
                schedule_scope='finite requests anchored to common refresh completion; true phase unobserved')
    return PhaseStdin()
