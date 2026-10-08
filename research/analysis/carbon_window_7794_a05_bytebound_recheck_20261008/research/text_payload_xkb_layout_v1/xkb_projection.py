from __future__ import annotations
import os
from pathlib import Path
import re
import subprocess
from Xlib import XK


def resolve_xkb(display_name: str, xauthority: str, layout: str, variant: str, out_dir: Path) -> str:
    env = os.environ.copy(); env['DISPLAY'] = display_name; env['XAUTHORITY'] = xauthority
    cmd = ['setxkbmap', '-layout', layout]
    if variant:
        cmd += ['-variant', variant]
    cmd += ['-print']
    src = subprocess.run(cmd, env=env, check=True, text=True, capture_output=True).stdout
    source = out_dir / 'layout.src.xkb'; resolved = out_dir / 'layout.resolved.xkb'
    source.write_text(src, encoding='utf-8')
    subprocess.run(['xkbcomp', '-xkb', '-w', '0', str(source), str(resolved)], check=True, text=True, capture_output=True)
    return resolved.read_text(encoding='utf-8')


def project_group1_two_levels(xkb_text: str, first_code: int, current_mapping: list[list[int]]) -> tuple[list[list[int]], int]:
    codes = {m.group(1): int(m.group(2)) for m in re.finditer(r'<([^>]+)>\s*=\s*(\d+)\s*;', xkb_text)}
    rows = [(list(row[:2]) + [0, 0])[:2] for row in current_mapping]
    matched = 0
    for m in re.finditer(r'key\s+<([^>]+)>\s*\{(.*?)\};', xkb_text, re.S):
        name, body = m.group(1), m.group(2)
        sm = re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]', body, re.S)
        if sm is None:
            sm = re.search(r'\[(.*?)\]', body, re.S)
        code = codes.get(name)
        if not sm or code is None or not (first_code <= code < first_code + len(rows)):
            continue
        values = []
        for token in [x.strip() for x in sm.group(1).split(',')][:2]:
            if token in ('', 'NoSymbol', 'VoidSymbol'):
                values.append(0); continue
            keysym = XK.string_to_keysym(token)
            if keysym == 0 and len(token) == 1:
                keysym = ord(token)
            values.append(int(keysym))
        while len(values) < 2:
            values.append(0)
        rows[code - first_code] = values
        matched += 1
    return rows, matched
