"""Read a retained receipt and its referenced PNG without executing input."""
import base64
import hashlib
import json
from pathlib import Path

from .receipt import receipt_view
from .receipt_image import select_image


def review(report_path, run_directory):
    view = receipt_view(report_path)
    # Parse the same bytes whose digest is presented to the caller.
    data = Path(view['source']['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != view['source']['sha256']:
        raise ValueError('report changed during review')
    report = json.loads(data)
    result = {'schema': 'agent-interface/review-v1', 'receipt': view,
              'image': None, 'authority': 'none'}
    try:
        native = None
        if report.get('schema') == 'agent-interface/runtime-observation-v1':
            native = report.get('observation')
            if native is None:
                result['image_status'] = 'no_observation'
                return result
            if not isinstance(native, dict):
                raise ValueError('invalid runtime observation')
            artifact = native.get('artifact')
            if not isinstance(artifact, dict):
                raise ValueError('runtime observation has no PNG artifact')
            if (artifact.get('mime_type') != 'image/png' or
                    not isinstance(native.get('sha256'), str) or
                    artifact.get('source_raw_sha256') != native['sha256']):
                raise ValueError('runtime capture identity mismatch')
            # The public observation has an ID, not an exchange sequence.
            # Use a local singleton selector index; never expose it as sequence.
            selected = select_image({'records': [{'event': 'observation',
                'sequence': 1, 'capture_ns': native.get('capture_started_ns'),
                'image': artifact.get('path')}]}, run_directory)
            selected.pop('sequence')
            selected['observation_id'] = report.get('observation_id')
            if selected['sha256'] != artifact.get('sha256'):
                raise ValueError('runtime image sha256 mismatch')
        else:
            selected = select_image(report, run_directory)
        if selected['status'] != 'image':
            result['image_status'] = 'no_observation'
            return result
        recorded = report.get('image')
        if isinstance(recorded, dict) and recorded.get('status') == 'image':
            for field in ('sequence', 'capture_ns', 'path', 'sha256'):
                if recorded.get(field) != selected[field]:
                    raise ValueError('report image identity mismatch: ' + field)
        image_bytes = Path(selected['path']).read_bytes()
        if hashlib.sha256(image_bytes).hexdigest() != selected['sha256']:
            raise ValueError('image changed during review')
        if not image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('referenced file is not a PNG')
        result['image'] = {'type': 'image', 'mimeType': 'image/png',
                           'data': base64.b64encode(image_bytes).decode('ascii')}
        result['image_reference'] = selected
        result['image_status'] = 'image'
    except Exception as error:
        # An unavailable image must never erase the action result or replay it.
        result.update(image_status='needs_review', image_error=str(error))
    return result
