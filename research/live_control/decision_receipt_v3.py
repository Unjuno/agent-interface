"""Add attention for any recorded terminal interruption, including completed status."""
import argparse
import json
from pathlib import Path
from decision_receipt_v2 import build as previous


def build(data):
    result = previous(data)
    result['format'] = 'decision-receipt-v3'
    for item in result['terminals']:
        terminal = item['record']
        if terminal.get('interruption') is not None or terminal.get('decision_reason'):
            result['attention'].append({'path': item['path'],
                                        'reason': 'recorded interruption/decision reason requires review regardless of terminal status'})
    result['detail_review_required'] = bool(result['attention'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    from report_pages_v2 import MAX_SOURCE
    with args.source.open('rb') as stream:
        data = stream.read(MAX_SOURCE + 1)
    print(json.dumps(build(data)))
