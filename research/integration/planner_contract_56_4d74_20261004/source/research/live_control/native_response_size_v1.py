"""Measure retained MCP text/PNG bytes and verify existing lossless receipt refs."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from receipt_references import expand_native_receipt


def measure(root):
    root = Path(root)
    raw_trace = (root/'responses.jsonl').read_bytes()
    output = []
    for line in raw_trace.splitlines():
        row = json.loads(line)
        blocks = row['result']['content']
        text = blocks[0]['text']
        meta = json.loads(text)
        # Use exactly the adapter's JSON serialization on both representations.
        assert json.dumps(meta, allow_nan=False) == text
        expanded = dict(meta)
        verified = False
        if 'receipt' in meta:
            receipt = expand_native_receipt(meta['receipt'])
            source = receipt['source']
            raw = (root/'allocation/run'/Path(source['path']).name).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == source['sha256']
            assert receipt['native_result'] == json.loads(raw)
            expanded['receipt'] = receipt
            verified = True
        png_bytes = sum(len(base64.b64decode(b['data'], validate=True))
                        for b in blocks if b['type'] == 'image')
        output.append({'id': row['id'], 'tool': row['tool'],
            'wire_line_bytes': len(line), 'text_utf8_bytes': len(text.encode('utf-8')),
            'expanded_text_utf8_bytes': len(json.dumps(expanded, allow_nan=False).encode('utf-8')),
            'png_bytes': png_bytes, 'receipt_reconstruction_verified': verified})
    current = sum(r['text_utf8_bytes'] for r in output)
    expanded = sum(r['expanded_text_utf8_bytes'] for r in output)
    return {'run': root.name, 'trace_sha256': hashlib.sha256(raw_trace).hexdigest(),
            'rows': output, 'text_utf8_bytes': current, 'expanded_text_utf8_bytes': expanded,
            'existing_reference_bytes_saved': expanded-current,
            'scope': 'text serialization bytes, not tokenizer/image tokens, inference cost or latency'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='+', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = json.dumps([measure(root) for root in args.runs], indent=2)+'\n'
    if args.output:
        with args.output.open('x', encoding='utf-8', newline='\n') as target:
            target.write(report)
    else:
        print(report, end='')
