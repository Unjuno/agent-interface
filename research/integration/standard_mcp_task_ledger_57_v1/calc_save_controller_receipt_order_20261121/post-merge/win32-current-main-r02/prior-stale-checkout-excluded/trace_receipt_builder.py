import json, sys, unittest
from pathlib import Path
repo = Path(sys.argv[1])
sys.path.insert(0, str(repo))
sys.path.insert(0, str(repo / 'research/integration/standard_mcp_task_ledger_57_v1'))
import runtime.guarded_x11_v1.calc_task_artifact_v1 as artifact
original = artifact.make_registered_calc_save_controller_receipt
rows = []
def traced(**kwargs):
    d, m, s = kwargs.get('descriptor'), kwargs.get('method_receipt'), kwargs.get('save_request')
    out = original(**kwargs)
    rows.append({
      'descriptor': {k:d.get(k) for k in ('profile_id','attempt_id','call_id')} if isinstance(d,dict) else type(d).__name__,
      'save_request': s if isinstance(s,dict) else type(s).__name__,
      'method_summary': ({'format':m.get('format'),'outcome':m.get('outcome'),'reason':m.get('reason'),'completed_transitions':m.get('completed_transitions'),'interface_id':m.get('interface_id'),'method':m.get('method'),'method_version':m.get('method_version'),'task_plan_sha256':m.get('task_plan_sha256'),'task_plan_interface':bool(m.get('task_plan_interface')),'critical_events':m.get('critical_events')} if isinstance(m,dict) else type(m).__name__),
      'parent_task_plan_sha256':kwargs.get('parent_task_plan_sha256'),
      'controller_minted':out is not None,
    })
    Path(sys.argv[2]).write_text(json.dumps(rows, indent=2, sort_keys=True), encoding='utf-8')
    return out
artifact.make_registered_calc_save_controller_receipt = traced
name='test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score'
suite=unittest.defaultTestLoader.loadTestsFromName(name)
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
