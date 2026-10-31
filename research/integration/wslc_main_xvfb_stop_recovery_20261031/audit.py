"""Verify retained source identity and bounded private-Xvfb observations."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

packet = Path(__file__).with_name('public.zip')
assert hashlib.sha256(packet.read_bytes()).hexdigest() == '67474ee6b0d57f6605455d09c46de0aee4c57d16ad428a4e68a552673c4c2c9d'
with ZipFile(packet) as z:
    manifest = json.loads(z.read('manifest.json'))
    assert set(z.namelist()) == set(manifest['files']) | {'manifest.json'}
    for name, expected in manifest['files'].items():
        assert hashlib.sha256(z.read(name)).hexdigest() == expected, name
    assert manifest['source_commit'] == '1ad8684ecc1cdbc70f627799c61290473c723503'
    before = json.loads(z.read('b01/out/launcher.json'))
    run = json.loads(z.read('b02/out/launcher.json'))
    receipt = json.loads(z.read('b02/out/receipt.json'))
    assert before['exit_code'] == 127 and not before['timeout']
    assert b'python: not found' in z.read('b01/out/stderr.bin')
    assert run['exit_code'] == 0 and not run['timeout']
    assert b'Ran 5 tests' in z.read('b02/out/stderr.bin')
    assert receipt['cancel_returned_before_server_resume']
    assert receipt['cancel_elapsed_s'] < receipt['conditions']['cancel_response_bound_s']
    assert receipt['cancel']['release_confirmed'] is False
    assert receipt['cancel']['replay_allowed'] is False
    assert receipt['cancellation_terminal']['result']['cleanup_status'] == 'UNKNOWN'
    assert receipt['synthetic_task_oracle']['status'] == 'fail'
    assert receipt['independent_readback_after_resume']['horizon_readback']['a'] is True
    assert receipt['recovery']['independent_task_oracle']['status'] == 'pass'
    assert receipt['recovery']['independent_task_oracle']['task_success'] is True
    assert receipt['recovery']['independent_readback']['horizon_readback'] == {'a': False, 'b': False}
    assert receipt['recovery']['elapsed_ms'] < 1000 * receipt['conditions']['recovery_bound_s']
    assert receipt['final_cleanup']['keys_down'] == {'a': False, 'b': False}
    print(json.dumps({'status':'audited','old_task':'fail','fresh_target_task':'pass',
      'cancel_seconds':receipt['cancel_elapsed_s'],
      'fresh_recovery_ms':receipt['recovery']['elapsed_ms'],
      'final_cleanup':receipt['final_cleanup']['status']}, indent=2))
