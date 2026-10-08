import ast,hashlib,json,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
from runtime.cli_v1 import mcp_server
from runtime.cli_v1.test_mcp_session import OwnedMCPTests
ROOT=Path(__file__).resolve().parents[3]
source=subprocess.run(['git','show','093b39fdab8d8cd04c422f8d9956deef1b40a692:runtime/cli_v1/mcp_server.py'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='present_management_report')
node.name='_baseline_present_management_report_for_diagnostic'
exec(compile(ast.Module(body=[node],type_ignores=[]),'baseline-present-management-report','exec'),vars(mcp_server))
with patch.object(mcp_server,'present_management_report',mcp_server._baseline_present_management_report_for_diagnostic):
    suite=unittest.TestSuite([OwnedMCPTests('test_management_capture_disagreement_withholds_image_on_call_and_lookup')])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'baseline_revision':'093b39fdab8d8cd04c422f8d9956deef1b40a692','baseline_module_sha256':hashlib.sha256(source.encode()).hexdigest(),'failures':len(result.failures),'errors':len(result.errors),'scope':'post-fix reproduction with exact historical management presenter, test-double backend; not the original pre-edit run'}))
if len(result.failures)!=3 or result.errors:raise SystemExit('unexpected baseline reproduction')
