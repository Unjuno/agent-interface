from pathlib import Path
root=Path(__file__).resolve().parent
probe=(root/'probe_controller_exception_01.py').read_text()
probe=probe.replace('def close(self):','def close(self, timeout=1):')
start=probe.index('try:\n    child.stdin.write',probe.index("(out/'BEFORE_EXTERNAL_CLEANUP.json')"))
end=probe.index("(out/'EXTERNAL_CLEANUP.json')",start)
probe=probe[:start]+'''cleanup={'actor':'probe checks controller cleanup; no external finish', 'child_exit':child.poll(), 'finish_sent':False}
if child.poll() is None:
    child.kill();child.wait(timeout=3)
    cleanup['emergency_probe_kill']=True
'''+probe[end:]
probe=probe.replace("assert pre['child_poll'] is None and pre['child_commands_present'] is False","assert pre['child_poll']==0 and pre['child_commands_present'] is True")
probe=probe.replace("assert pre['fake_planner_close_present'] is False","assert pre['fake_planner_close_present'] is True")
(root/'probe_controller_exception_02.py').write_bytes(probe.encode())
driver=(root/'run_controller_exception_01.py').read_text()
driver=driver.replace('controller-exception-construction-01','controller-exception-construction-02').replace('ai59-4d74-exception01','ai59-4d74-exception02').replace('probe_controller_exception_01.py','probe_controller_exception_02.py').replace('run_controller_exception_01.py','run_controller_exception_02.py')
driver=driver.replace("'doom_source_refresh_v1.py',","'doom_source_refresh_v1.py','doom_controller_failure_cleanup_v1.py',")
(root/'run_controller_exception_02.py').write_bytes(driver.encode())
