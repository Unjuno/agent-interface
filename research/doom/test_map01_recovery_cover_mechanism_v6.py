import importlib.util
import sys
import types
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load():
    base=types.SimpleNamespace(ALLOCATION_ID='v5',EXPECTED_WORKFLOW_PATH='v5',_run_arm=lambda *a:None,main=lambda:None)
    v5=types.ModuleType('map01_recovery_cover_mechanism_v5_runner');v5.configure=lambda:base
    sys.modules['map01_recovery_cover_mechanism_v5_runner']=v5
    spec=importlib.util.spec_from_file_location('v6',HERE/'map01_recovery_cover_mechanism_v6_runner.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod,base


def test_configure_new_allocation_and_workflow():
    mod,base=load();got=mod.configure();assert got is base
    assert base.ALLOCATION_ID=='map01-recovery-cover-mechanism-live-v6-01'
    assert base.EXPECTED_WORKFLOW_PATH=='.github/workflows/map01-recovery-cover-mechanism-live-v6-01.yml'
    assert callable(base._run_arm)


def test_source_orders_planner_end_before_cleanup():
    text=(HERE/'map01_recovery_cover_mechanism_v6_runner.py').read_text()
    marker='planner_end_ns = session.runtime_clock()'
    release_wait='session.wait(lambda r: r.get("event") in {"input_released", "input_release_unverified"}'
    boundary=text.index(marker)
    post_timer_if=text.index('if fallback_terminal is None:', boundary)
    assert boundary < post_timer_if
    assert text.index(release_wait, post_timer_if) > boundary


def test_boundary_phase_is_retained():
    text=(HERE/'map01_recovery_cover_mechanism_v6_runner.py').read_text()
    assert '"end_boundary_phase": "immediately_after_delay_before_fallback_cleanup"' in text

if __name__=='__main__':
    tests=sorted((n,f) for n,f in globals().items() if n.startswith('test_'))
    for n,f in tests:f();print('PASS',n)
    print('PASS total',len(tests))
