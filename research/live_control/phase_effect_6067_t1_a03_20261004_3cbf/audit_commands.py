"""Canonical saved-only launch; checked before any external write/execution."""
from pathlib import Path
from runner import VM,IMAGE
import reference as ref

def commands(f):
    mode=f['mode'];ref.need(mode in ('readiness','formal'),'closed audit mode')
    from protocol import freeze_filename
    freeze_file=freeze_filename(mode,f.get('freeze_file'))
    prefix=['orbctl','run','-m',VM]
    name='phase-effect-6067-a03-'+mode+'-3cbf-audit'
    argv=['python3','-B','/src/saved_audit.py','--raw','/raw','--out','/out/result',
          '--freeze','/src/'+freeze_file]
    launch=prefix+['-u','root','docker','run','--pull=never','--name',name,'--label','owner=3cbf',
         '--label','stage='+mode+'-saved-audit','--user','501:501','--cpus','1','--memory','512m',
         '--memory-swap','512m','--pids-limit','64','--network','none','--read-only','--cap-drop','ALL',
         '--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=64m',
         '--mount','type=bind,src='+f['guest_source']+',dst=/src,readonly',
         '--mount','type=bind,src='+f['guest_wrapper']+',dst=/raw,readonly',
         '--mount','type=bind,src='+f['guest_audit']+',dst=/out',IMAGE]+argv
    return {'auditor_command':launch,'audit_native_argv':argv,
            'audit_stage_command':prefix+['cp','-a','/mnt/mac'+f['host_raw'],f['guest_wrapper']],
            'audit_mkdir_command':prefix+['mkdir',f['guest_audit']],
            'audit_inspect_command':prefix+['-u','root','docker','inspect','--format','{{json .}}',name],
            'audit_copy_command':prefix+['cp','-a',f['guest_audit']+'/result','/mnt/mac'+f['host_audit']+'/result']}

def admit_audit_commands(f):
    for key,value in commands(f).items():ref.join(f[key],value,'prelaunch canonical '+key)

def admit_freeze_bytes(supplied,executed):
    ref.need(type(supplied) is bytes and type(executed) is bytes and bool(supplied) and supplied==executed,
             'supplied freeze identical to executed source freeze')
