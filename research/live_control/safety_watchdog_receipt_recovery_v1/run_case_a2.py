from pathlib import Path
base=Path(__file__).with_name('run_case.py')
s=base.read_text()
old="wd_out,wd_err=wd.communicate(timeout=2); wd_debug=json.loads(wd_out.strip())"
new="wd_out,wd_err=wd.communicate(timeout=2); wd_lines=[x for x in wd_out.splitlines() if x.strip()]; wd_debug=json.loads(wd_lines[-1])"
if s.count(old) != 1:
    raise RuntimeError('A1 framing target not unique')
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s.replace(old,new),str(base),'exec'),ns,ns)
