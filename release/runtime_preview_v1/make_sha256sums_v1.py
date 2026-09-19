from __future__ import annotations
import argparse, hashlib
from pathlib import Path

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--out', default='SHA256SUMS')
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / args.out
    rows = []
    for path in sorted(item for item in root.rglob('*') if item.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel == args.out or rel.startswith('.git/'):
            continue
        rows.append(f'{sha256(path)}  {rel}')
    output.write_text('\n'.join(rows) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(rows)} entries -> {output}')

if __name__ == '__main__':
    main()
