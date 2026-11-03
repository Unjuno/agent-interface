import ast, pathlib, sys
from runtime.cli_v1.mcp_server import create_server
from runtime.guarded_x11_v1.calc_profile_v1 import verify_saved_fods, verify_saved_fods_bytes
from runtime.guarded_x11_v1.calc_launcher_v1 import CalcLaunchSupervisor
p=pathlib.Path('/evidence/r84-a8/experiment.py')
ast.parse(p.read_text(encoding='utf-8'))
assert callable(verify_saved_fods) and callable(verify_saved_fods_bytes)
assert callable(create_server) and callable(CalcLaunchSupervisor)
print('preflight=PASS')
print('network=none; no X server, Calc process, MCP task, or input started')