# Construction-only host check; fetches frozen Python source into memory and writes no local files.
$ErrorActionPreference = 'Stop'
$base = 'https://raw.githubusercontent.com/Unjuno/agent-interface/6463a31cdd89e38e6023c924b182798a99f19b39/research/analysis/planner_hysteresis_5352_t0_v1/'
$sim = (Invoke-WebRequest -UseBasicParsing -Uri ($base + 'simulator.py')).Content
$tests = (Invoke-WebRequest -UseBasicParsing -Uri ($base + 'test_simulator.py')).Content
$audit = (Invoke-WebRequest -UseBasicParsing -Uri ($base + 'audit.py')).Content
$env:UJUN5352_SIM_B64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($sim))
$env:UJUN5352_TEST_B64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($tests))
$env:UJUN5352_AUDIT_B64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($audit))
$launcher = @'
import base64,hashlib,os,sys,types,unittest
sim=base64.b64decode(os.environ["UJUN5352_SIM_B64"])
tests=base64.b64decode(os.environ["UJUN5352_TEST_B64"])
audit=base64.b64decode(os.environ["UJUN5352_AUDIT_B64"])
compile(sim,"<frozen-simulator>","exec")
compile(audit,"<frozen-auditor>","exec")
module=types.ModuleType("simulator")
exec(compile(sim,"<frozen-simulator>","exec"),module.__dict__)
sys.modules["simulator"]=module
test_module=types.ModuleType("frozen_tests")
exec(compile(tests,"<frozen-tests>","exec"),test_module.__dict__)
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_module))
for name,source in (("simulator",sim),("tests",tests),("auditor",audit)):
 print(name+"_sha256="+hashlib.sha256(source).hexdigest())
raise SystemExit(0 if result.wasSuccessful() else 1)
'@
$launcherB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($launcher))
python -B -c "exec(__import__('base64').b64decode('$launcherB64'))"
if ($LASTEXITCODE -ne 0) { throw "construction checks failed with exit $LASTEXITCODE" }
