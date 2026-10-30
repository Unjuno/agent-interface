"""Read-only byte audit of committed evidence; run inside the source Git repository."""
import hashlib
import json
import subprocess
import sys

MAIN = '0989d0bff9dfebbf7803d926b4699b6b92e35499'
PARENT = 'c6451f14fbd26787ff87217b414d8cf75f1255f4'
RESULT = 'runtime/results/golden-desktop-app-server-v3-live-01/'
PREVIOUS = 'research/integration/integrated_efficiency_current_main_audit_20261029/audit.json'

def git_blob(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], stderr=subprocess.DEVNULL)

def digest(blob):
    return hashlib.sha256(blob).hexdigest()

def main():
    # The prior audit packet was untracked in this checkout; input is supplied
    # explicitly and its own hash is printed for reproducibility.
    previous_bytes = open(sys.argv[1], 'rb').read()
    previous = json.loads(previous_bytes)
    manifest = json.loads(git_blob(MAIN, RESULT + 'retention-manifest.json'))
    rows = []
    for entry in manifest['files']:
        try:
            blob = git_blob(MAIN, RESULT + entry['path'])
            actual, size = digest(blob), len(blob)
        except subprocess.CalledProcessError:
            actual, size = None, None
        rows.append({'path': entry['path'], 'expected': entry['sha256'],
                     'actual': actual, 'expected_bytes': entry['bytes'],
                     'actual_bytes': size,
                     'match': actual == entry['sha256'] and size == entry['bytes']})
    sources = []
    for row in previous['v3_preregistered_sources']['rows']:
        try:
            blob = git_blob(PARENT, row['path'])
            actual = digest(blob)
            crlf = digest(blob.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        except subprocess.CalledProcessError:
            actual = None
            crlf = None
        sources.append({'path': row['path'], 'expected': row['expected'],
                        'parent_git_sha256': actual, 'match': actual == row['expected'],
                        'parent_crlf_sha256': crlf, 'crlf_match': crlf == row['expected']})
    result = {'main': MAIN, 'parent': PARENT, 'previous_audit_sha256': digest(previous_bytes),
              'manifest_sha256': digest(git_blob(MAIN, RESULT + 'retention-manifest.json')),
              'manifest_rows': rows, 'source_rows': sources}
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
