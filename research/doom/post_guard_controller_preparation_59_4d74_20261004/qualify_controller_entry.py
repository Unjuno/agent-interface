from pathlib import Path
import os,json,hashlib,sys
os.environ.update(GAME_SOURCE='/study/current-game-source-05',HOST_EMPTY_CWD='C:/owned-empty',GUEST_OUTPUT_ROOT='/out',HOST_OUTPUT_ROOT='C:/owned-output',RELAY_COMMAND_JSON=json.dumps([sys.executable,'/study/real_file_stdio_proxy.py']),QUALIFIED_WAD_PATH='/study/fixture-input/freedoom2.wad',QUALIFIED_CONTROLLER_ASSETS='/study/current-game-source-05/research/doom')
sys.path.insert(0,'/study')
import portable_controller_entry as entry
c=entry.install();image=Path('/out/probe.png');image.write_bytes(Path('/study/fixture-input/source.png').read_bytes())
host=entry.host_path(image);refused=False
try:entry.host_path(Path('/study/fixture-input/source.png'))
except ValueError:refused=True
r={'scope':'entry construction only; zero game/model/input starts','image_host_path':host,'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'outside_output_refused':refused,'host_cwd':entry.host_path(c.REPO),'command':c.app_server_command(),'session_script_exists':(c.HERE/'session_map01_v12.py').is_file(),'instructions_exists':(c.HERE/'map01_motor_responder_v10.txt').is_file(),'schema_exists':(c.HERE/'map01_cover_policy_schema_v6.json').is_file()}
Path('/out/RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sys.exit(0 if refused and all(r[k] for k in ['session_script_exists','instructions_exists','schema_exists']) else 1)
