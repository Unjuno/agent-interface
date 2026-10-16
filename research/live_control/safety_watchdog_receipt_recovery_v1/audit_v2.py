from pathlib import Path
base=Path(__file__).with_name('audit.py')
s=base.read_text()
old="if not (receipt['verified_empty_ns'] < j['journal_write_start_ns'] <= j['journal_write_done_ns'] < rec['recovered_publish_ns']): errors.append([cid,'journal_order'])"
new="if not (receipt['verified_empty_ns'] < j['journal_write_start_ns'] <= receipt['journal_write_done_ns'] < rec['recovered_publish_ns']): errors.append([cid,'journal_order'])"
if s.count(old) != 1:
    raise RuntimeError('frozen audit correction target not unique')
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s.replace(old,new),str(base),'exec'),ns,ns)
