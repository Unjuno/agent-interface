"""Sanitize one-use X11 credentials before retaining Docker inspect evidence."""
import hashlib
import json
import subprocess
from pathlib import Path

def inspect_to_file(container, target):
    raw = subprocess.run(['docker', 'inspect', container], check=True, capture_output=True, text=True).stdout
    records = json.loads(raw)
    redacted = []
    for record in records:
        config = record.get('Config', {})
        envs = []
        for item in config.get('Env', []):
            if item.startswith('X11_COOKIE='):
                digest = hashlib.sha256(item.partition('=')[2].encode('ascii')).hexdigest()
                envs.append(f'X11_COOKIE_SHA256={digest}')
                redacted.append({'field': 'Config.Env.X11_COOKIE', 'sha256': digest})
            else:
                envs.append(item)
        config['Env'] = envs
        for mount in record.get('Mounts', []):
            if mount.get('Source'):
                mount['Source'] = '<redacted>/' + str(mount['Source']).replace('\\', '/').rstrip('/').split('/')[-1]
        host = record.get('HostConfig', {})
        binds = []
        for bind in host.get('Binds') or []:
            parts = bind.split(':')
            if len(parts) >= 4 and len(parts[0]) == 1:
                source = ':'.join(parts[:2])
                destination, mode = parts[2], ':'.join(parts[3:])
            elif len(parts) >= 3:
                source, destination, mode = parts[0], parts[1], ':'.join(parts[2:])
            else:
                binds.append('<redacted-bind>')
                continue
            basename = source.replace('\\', '/').rstrip('/').split('/')[-1]
            binds.append(f'<redacted>/{basename}:{destination}:{mode}')
        if 'Binds' in host:
            host['Binds'] = binds
    Path(target).write_text(json.dumps(records, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return records[0], redacted
