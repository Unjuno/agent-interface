"""Retain parent-held save-controller inputs during one offline Docker run."""
import json
from pathlib import Path
import unittest

from runtime.guarded_x11_v1 import calc_task_artifact_v1 as artifact_module

def main():
    original = artifact_module.make_registered_calc_save_controller_receipt

    def traced(**kwargs):
        receipt = original(**kwargs)
        Path('/evidence/docker-save-controller-inputs-r02.json').write_text(
            json.dumps({'inputs': kwargs, 'receipt': receipt}, sort_keys=True,
                       indent=2, default=repr, allow_nan=False) + '\n',
            encoding='utf-8')
        return receipt

    artifact_module.make_registered_calc_save_controller_receipt = traced
    suite = unittest.defaultTestLoader.loadTestsFromName(
        'test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.'
        'test_fake_app_server_generation_is_recorded_through_calc_profile_and_score')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
