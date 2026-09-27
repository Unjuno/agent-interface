import json,shutil,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
# This test operates only on synthetic retained-like bytes; it starts no X server.
def build(root):
    plan=json.loads((HERE/'plan.json').read_text());
    sample='''xkb_keymap {\nxkb_keycodes "x" { minimum=8; maximum=255; <AD01> = 24; <RALT> = 108; };\nxkb_symbols "x" { key <AD01> { type="FOUR_LEVEL_SEMIALPHABETIC", symbols[Group1]= [ q, Q, at, Greek_OMEGA ] }; key <RALT> { [ ISO_Level3_Shift ] }; };\n};\n'''
    # Hash mismatch is expected for this synthetic fixture, so audit should fail.
    for i in range(3):
        d=root/f'arm-{i:02d}';d.mkdir(parents=True);(d/'de.resolved.xkb').write_text(sample);(d/'baseline.server.xkb').write_text('a');(d/'after.server.xkb').write_text('a')
        r={'resolved_sha256':'bad','input_operations':0,'baseline_server_sha256':'bad','after_server_sha256':'bad','server_dump_changed':False,'xkeyboard_present':True,'integrity':True,'apply':{'returncode':0},'live_core_map_changed':False,'live_ad01_level3_at':False,'decision':'SETUP_BLOCKED_NATIVE_XKB_APPLY'};(d/'result.json').write_text(json.dumps(r))
    (root/'summary.json').write_text(json.dumps({'decision':'SETUP_BLOCKED_NATIVE_XKB_APPLY','input_operations':0}))
    p=subprocess.run([sys.executable,str(HERE/'audit.py'),str(root),'--plan',str(HERE/'plan.json')]); return p.returncode
with tempfile.TemporaryDirectory() as td:
    assert build(Path(td))==2
print('PASS_TEST_AUDIT')
