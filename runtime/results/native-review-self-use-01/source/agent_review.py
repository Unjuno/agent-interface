"""Read a complete retained report and its referenced image in one response."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys

from receipt_image import select_image

# Direct script execution and import from the research client are both supported.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.cli_v1.receipt import receipt_view


def review_native(report_path, run_directory):
    """Present an explicit native observation/feedback without recapturing it."""
    path = Path(report_path).resolve(strict=True)
    data = path.read_bytes()
    report = json.loads(data)
    if not isinstance(report, dict):
        raise ValueError('native report must be an object')
    result = {'schema': 'agent-interface/review-v1', 'authority': 'none',
              'receipt': {'source': {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()},
                          'native_result': report}, 'image': None}
    try:
        observation = report if 'native' in report else report.get('observation')
        if observation is None:
            result['image_status'] = 'no_observation'
            return result
        native = observation['native']
        artifact = native['artifact']
        if (artifact['source_raw_sha256'] != native['sha256'] or
                observation['capture_ns'] != native['capture_started_ns']):
            raise ValueError('native capture identity mismatch')
        selected = select_image({'records': [{'event': 'observation',
            'sequence': observation['sequence'], 'capture_ns': observation['capture_ns'],
            'image': artifact['path']}]}, run_directory)
        image_bytes = Path(selected['path']).read_bytes()
        digest = hashlib.sha256(image_bytes).hexdigest()
        if digest != artifact['sha256'] or digest != selected['sha256']:
            raise ValueError('native image sha256 mismatch')
        if artifact['mime_type'] != 'image/png' or not image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('native artifact is not a PNG')
        result.update(image_status='image', image_reference=selected,
                      image={'type': 'image', 'mimeType': 'image/png',
                             'data': base64.b64encode(image_bytes).decode('ascii')})
    except Exception as error:
        result.update(image_status='needs_review', image_error=str(error))
    return result


def review(report_path, run_directory, *, compact=False):
    view = receipt_view(report_path)
    # Parse the same bytes whose digest is presented to the caller.
    data = Path(view['source']['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != view['source']['sha256']:
        raise ValueError('report changed during review')
    report = json.loads(data)
    if compact:
        from receipt_references import compact_receipt
        view = compact_receipt(view)
    result = {'schema': 'agent-interface/review-v1', 'receipt': view,
              'image': None, 'authority': 'none'}
    try:
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True)
    parser.add_argument('--run-directory', required=True)
    parser.add_argument('--compact', action='store_true', help='replace exact duplicate event copies with local references')
    parser.add_argument('--native', action='store_true', help='present an exact native observation or feedback report')
    args = parser.parse_args()
    if args.native and args.compact:
        parser.error('--compact is only supported for event receipts')
    result = (review_native(args.report, args.run_directory) if args.native else
              review(args.report, args.run_directory, compact=args.compact))
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
