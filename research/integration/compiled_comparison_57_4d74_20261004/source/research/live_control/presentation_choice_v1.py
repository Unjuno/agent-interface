"""Choose presentation before emitting; output failures never trigger retries."""
import hashlib
import json
from pathlib import Path
from composed_result_v1 import build, decode
from shared_result_v1 import canonical, unique_pairs
from presentation_emission_v1 import emit


def choose(data, composer=build, decoder=decode):
    original = json.loads(data, object_pairs_hook=unique_pairs)
    baseline = canonical(original)
    meta = dict(source_sha256=hashlib.sha256(data).hexdigest(),
                original_bytes=len(baseline.encode('utf-8')))
    try:
        candidate = composer(data)
        if canonical(decoder(candidate)) != baseline:
            raise ValueError('presentation reconstruction mismatch')
        size = len(canonical(candidate).encode('utf-8'))
        if size < meta['original_bytes']:
            return candidate, dict(meta, choice='composed', chosen_bytes=size)
        return original, dict(meta, choice='original_no_size_benefit', chosen_bytes=meta['original_bytes'])
    except Exception as error:
        # Only preparation is caught. The original JSON has already validated.
        fallback = dict(format='presentation-fallback-v1', result=original,
            presentation_error=dict(type=type(error).__name__, message=str(error)),
            scope='Formatting failed; original result retained. No operation replay or task-status change.')
        return fallback, dict(meta, choice='original_with_presentation_error',
                              chosen_bytes=len(canonical(fallback).encode('utf-8')))


def deliver(data, stream, directory, composer=build, decoder=decode):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False)
    value, metadata = choose(data, composer, decoder)
    (root/'choice.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    # Outside the fallback catch: a partially written frame cannot be replaced.
    return emit(value, stream, root/'emission')
