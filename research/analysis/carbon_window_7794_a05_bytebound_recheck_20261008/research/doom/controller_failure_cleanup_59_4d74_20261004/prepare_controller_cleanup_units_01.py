from pathlib import Path
root=Path(__file__).resolve().parent
s=(root/'run_source_refresh_construction_03.py').read_text()
s=s.replace('source-refresh-construction-03','controller-cleanup-units-01').replace('source-refresh03','cleanup-units01')
s=s.replace('names=[',"names=['doom_controller_failure_cleanup_v1.py','test_controller_failure_cleanup_v1.py',")
s=s.replace("'test_source_refresh_v1','test_map01_overlap_controller_v39'", "'test_controller_failure_cleanup_v1','test_source_refresh_v1','test_map01_overlap_controller_v39'")
(root/'run_controller_cleanup_units_01.py').write_bytes(s.encode())
