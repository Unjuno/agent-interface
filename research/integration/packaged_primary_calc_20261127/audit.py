"""Audit the retained packaged-primary Calc trial without extracting the archive."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
ARCHIVE_SHA256 = '1d7b491b7289a5de38ce9ea13b6cfc40cef9b429ab14cd8a68423cfffbf7d87d'
SEAL_SHA256 = '66a2f7c10554724f65bd525979dce0d141a39845e64911677807908148fbc702'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

raw = (ROOT / 'trial.zip').read_bytes()
require(digest(raw) == ARCHIVE_SHA256, 'archive digest mismatch')
with zipfile.ZipFile(ROOT / 'trial.zip') as z:
    names = z.namelist()
    require(len(names) == len(set(names)), 'duplicate archive member')
    require(digest(z.read('seal.json')) == SEAL_SHA256, 'seal digest mismatch')
    seal = json.loads(z.read('seal.json'))
    entries = {row['path']: row for row in seal['files']}
    require(len(entries) == len(seal['files']) and set(names) == set(entries) | {'seal.json'}, 'seal member mismatch')
    for name, row in entries.items():
        data = z.read(name)
        require(len(data) == row['bytes'] and digest(data) == row['sha256'], 'sealed bytes differ: ' + name)
    registration = json.loads(z.read('registration.json'))
    for name, row in registration['files'].items():
        data = z.read(name)
        require(len(data) == row['bytes'] and digest(data) == row['sha256'], 'registered bytes differ: ' + name)
    def response(i, tool):
        row = json.loads(z.read(f'output/exchange/original-reply-{i}.json'))
        require(row['tool'] == tool and row['result']['isError'] is False, 'unexpected reply')
        return json.loads(row['result']['content'][0]['text'])
    for i, method in enumerate(('observe','review','mint','acknowledgeText','input','call'), 1):
        row = json.loads(z.read(f'output/exchange/request-{i}.json'))
        require(row['id'] == i and row['method'] == method, 'command order differs')
    observation = response(1, 'interface_guarded_observe')
    mint = response(3, 'interface_guarded_mint')
    action = response(5, 'interface_guarded_input')
    close = response(6, 'interface_close')
    require(observation['status'] == 'observed' and observation['input_dispatched'] is False, 'observation differs')
    require(mint['status'] == 'minted' and action['status'] == 'completed' and close['status'] == 'closed', 'outcome differs')
    require(action['result']['recovery_required'] is False, 'recovery required')
    releases = action['result']['execution']['releases']
    require(bool(releases) and all(r['verified'] is True and r['keys_down'] == [] and r['buttons_down'] == [] for r in releases), 'release unverified')
    for i, response_row in ((1, observation), (5, action)):
        require(digest(z.read(f'output/exchange/image-{i}-1.png')) == response_row['source']['native']['artifact']['sha256'], 'image differs')
    neutral = json.loads(z.read('output/final-observed-neutral.json'))
    require(neutral == {'keys_down': [], 'buttons_mask': 0}, 'X input not neutral')
    ns = {'t':'urn:oasis:names:tc:opendocument:xmlns:table:1.0','o':'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}
    saved = z.read('output/saved.fods')
    cell = ET.fromstring(saved).find('.//t:table/t:table-row/t:table-cell', ns)
    require(cell is not None and cell.get('{'+ns['o']+'}value') == '271' and cell.get('{'+ns['t']+'}formula') is None, 'saved A1 differs')
    host_source = json.loads((ROOT / 'host-source-verification.json').read_text(encoding='utf-8-sig'))
    require(host_source['commit'] == 'd3a6c8ecc7e75a7abdc0af4ac9cbd256ff3fe2c0', 'host source ref differs')
    require(len(host_source['matched_host_files']) == 8, 'host source file count differs')
    for row in host_source['matched_host_files']:
        data = z.read('host/' + row['path'])
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(blob == row['blob'], 'host source differs')
    with zipfile.ZipFile(__import__('io').BytesIO(z.read('runtime.pyz'))) as runtime:
        build = json.loads(runtime.read('BUILD.json'))
        source_check = json.loads((ROOT / 'source-verification.json').read_text(encoding='utf8'))
        for row in build['source_files']:
            expected = source_check['files'][row['path']]['sha256']
            require(row['sha256'] == expected and digest(runtime.read(row['path'])) == expected, 'runtime source differs')
    print(json.dumps({'status':'audited','a1':271,'saved_sha256':digest(saved),'verified_release':True,'final_x_neutral':True,'runtime_source_files_checked':len(build['source_files']),'model_calls':0}, sort_keys=True))
