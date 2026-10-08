from pathlib import Path
import json

out=Path('/var/tmp/agent-interface-evidence-storage-main/runtime/results/original-presentation-live-01')
projection=json.loads((out/'usage-whole.json').read_text())
window=projection['windows'][0]
indices={window['calls'][0]['source_line']:'begin',window['calls'][-1]['source_line']:'end'}
actual={}
with Path(projection['source_session']).open(encoding='utf-8') as source:
    for index,line in enumerate(source,1):
        if index not in indices:continue
        row=json.loads(line)
        if row['payload']['type']!='custom_tool_call':raise ValueError('boundary is not a tool call')
        actual[indices[index]]=row['payload']['input']
        if len(actual)==2:break
if '/keeper.py /var/tmp/' not in actual['begin'] or '/case immediate' not in actual['begin']:
    raise ValueError('begin is not actual launch')
if 'getextrema' not in actual['end'] or 'tools.view_image' not in actual['end']:
    raise ValueError('end is not terminal oracle plus original image view')
if any('project-original-live-usage.py' in value for value in actual.values()):
    raise ValueError('selector matched itself')
(out/'usage-boundary-check.json').write_text(json.dumps({'status':'PASS',
    'actual_launch_boundary':True,'actual_terminal_oracle_image_boundary':True,
    'self_matching_selector_excluded':True,'scaffold_build_excluded':True,
    'later_accounting_publication_excluded':True},indent=2)+'\n')
workspace=Path('/mnt/c/Users/junny/Documents/Codex/2026-09-27/files-mentioned-by-the-user-codex')
(out/'project_usage.py').write_text((workspace/'project-original-live-usage.py').read_text())
(out/'check_usage_boundaries.py').write_text((workspace/'check-original-live-boundaries.py').read_text())
(out/'usage-boundary-check-first-failure.txt').write_text('The first supplementary boundary checker used the window end output record as if it were a call input, causing KeyError: input. Actual token-source replay had already passed (39 lines, 13 responses). The corrected checker uses first/last call source lines. Original token projection is unchanged. No live case or action was repeated.\n')
print('PASS: actual call-input boundaries, not projection-generator or output records')
