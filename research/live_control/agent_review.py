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
    args = parser.parse_args()
    print(json.dumps(review(args.report, args.run_directory, compact=args.compact), allow_nan=False))


if __name__ == '__main__':
    main()
