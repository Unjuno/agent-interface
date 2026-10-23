"""Write a byte-exact SHA256SUMS over this retained packet."""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = []
for path in sorted((p for p in HERE.rglob('*') if p.is_file() and p.name != 'SHA256SUMS'),
                   key=lambda p:p.relative_to(HERE).as_posix()):
    rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(HERE).as_posix()}")
(HERE/'SHA256SUMS').write_text('\n'.join(rows)+'\n',encoding='utf-8',newline='\n')
print(f'files={len(rows)}')
