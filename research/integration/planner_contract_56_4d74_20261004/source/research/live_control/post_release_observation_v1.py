"""Two passive samples after verified release; equality is not application readiness."""
import time


def collect(backend, emit, identifier, index):
    started = time.perf_counter_ns()
    result = dict(captures=0, sequences=[], equal_sample_pair=False, error=None,
                  authority='none; no input or lease renewal',
                  scope='two samples 80ms apart; not readiness or semantic completion')
    previous = None
    try:
        for _ in range(2):
            time.sleep(.08)
            backend.snapshot(identifier, index)
            result['captures'] += 1
            result['sequences'].append(backend.sequence)
            frame = backend.decoder.frame
            sample = (frame, backend.observed_pointer)
            result['equal_sample_pair'] = previous is not None and previous == sample
            # Pointer binding is a new dict for each snapshot in this backend.
            previous = sample
    except Exception as exc:
        result['error'] = repr(exc)
    result['elapsed_ms'] = (time.perf_counter_ns() - started) / 1e6
    return result
