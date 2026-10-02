import asyncio, hashlib, json, os, subprocess, sys, tempfile, zipfile
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import openpyxl

root = Path(sys.argv[1]).resolve()
archive = root / 'runtime.pyz'
work = root / 'probe'
work.mkdir(exist_ok=False)
def save(name, value):
    (root/name).write_text(json.dumps(value, indent=2, default=str)+'\n')

async def probe(mode):
    targets = work/(mode+'-targets.json')
    targets.write_text('{"app":1}\n')
    params = StdioServerParameters(command=sys.executable, args=[str(archive), 'mcp',
        '--targets', str(targets), '--output-directory', str(work/(mode+'-calls')),
        '--session-mode', mode, '--display', ':29999'])
    with (root/(mode+'-stderr.log')).open('w') as stderr:
        async with stdio_client(params, errlog=stderr) as streams:
            async with ClientSession(*streams) as session:
                initialized = await session.initialize()
                listed = await session.list_tools()
                save(mode+'-schemas.json', listed.model_dump(mode='json'))
                return {'initialized': initialized.model_dump(mode='json'),
                    'tools': [t.name for t in listed.tools],
                    'input_calls': 0, 'native_connection_requested': False}

async def main():
    # Portable doctor runs outside the repository, with no configured display.
    doctor = subprocess.run([sys.executable, str(archive), 'doctor', '--check-dependencies'],
        cwd=work, env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','DISPLAY')},
        capture_output=True, text=True)
    (root/'doctor.stdout.json').write_text(doctor.stdout)
    (root/'doctor.stderr.log').write_text(doctor.stderr)
    if doctor.returncode:
        raise RuntimeError('doctor failed: '+str(doctor.returncode))
    sys.path.insert(0,str(archive))
    from runtime.guarded_x11_v1 import compiled
    compiled_path = compiled.__file__
    if not compiled_path.startswith(str(archive)):
        raise RuntimeError('compiled imported from checkout instead of archive')
    workbook = openpyxl.Workbook()
    workbook.active['A1']=317
    workbook.active['A2']=529
    path=work/'scorer-control.xlsx'
    workbook.save(path)
    scored=openpyxl.load_workbook(path,read_only=True,data_only=True)
    values=[scored.active['A1'].value,scored.active['A2'].value]
    scored.close()
    if values != [317,529]: raise RuntimeError('scorer control failed')
    modes={mode: await probe(mode) for mode in ('persistent-x11','guarded-x11')}
    save('admission.json', {'status':'PASS_SETUP_ONLY',
        'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'python':sys.version,'openpyxl':openpyxl.__version__,
        'compiled_module':compiled_path,'scorer_control_values':values,
        'modes':modes,'live_gui':False,'provider_schema_preflight':'unverified',
        'comparison':'not_allocated','model_usage':None,
        'compiled_public_tool': any('compiled' in name for row in modes.values() for name in row['tools']),
        'scope':'SDK metadata admission and offline scorer only; no GUI/effect/performance evidence'})

asyncio.run(main())
