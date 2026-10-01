import asyncio,json,sys,zipfile
from pathlib import Path
from jsonschema import Draft202012Validator
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
root=Path(__file__).resolve().parent
work=root/'next-schema-preflight';work.mkdir(exist_ok=False)
def save(name,value):(work/name).write_text(json.dumps(value,indent=2)+'\n')
# This is a prospective syntax template, not a renewed lease/current GUI request.
program={'schema':'agent-interface/program-v1','program_id':'next-calc-enter-save',
 'source':{'observation_seq':1,'binding_revision':1},
 'authority':{'lease_id':'syntax-only','expires_at_ns':1},
 'terminal':{'release_all_required':True},'ops':[
 {'op':'focus','target':'app'},{'op':'text','text':'317','gap_ms':20},
 {'op':'key_chord','keys':['ENTER']},{'op':'wait_update','timeout_ms':100},
 {'op':'text','text':'529','gap_ms':20},{'op':'key_chord','keys':['ENTER']},
 {'op':'wait_update','timeout_ms':100},{'op':'key_chord','keys':['CTRL','s']},
 {'op':'release_all'}]}
plans={
 'interface_dispatch':{'program':program,'current_observation_seq':1,'current_binding_revision':1,
   'compact':True,'report_refs':True,'detail':'summary','inspect_after':'app',
   'inspect_after_region':[0,0,1280,800],'inspect_after_wait_ms':100},
 'interface_inspect_target':{'target':'app','screen_region':[0,0,1280,800]},
 'interface_review_target':{'target':'app','window_id':1,'review_id':'syntax-only',
   'screen_region':[0,0,1280,800]},'interface_clock':{},'interface_close':{}}
async def main():
 targets=work/'targets.json';targets.write_text('{"app":1}\n')
 params=StdioServerParameters(command=sys.executable,args=[str(root/'runtime.pyz'),'mcp',
 '--targets',str(targets),'--output-directory',str(work/'calls'),
 '--session-mode','persistent-x11','--display',':29999'])
 with (work/'server.stderr').open('w') as err:
  async with stdio_client(params,errlog=err) as streams:
   async with ClientSession(*streams) as session:
    await session.initialize();listed=await session.list_tools()
    schemas={t.name:t.inputSchema for t in listed.tools}
    save('actual-schemas.json',listed.model_dump(mode='json'))
    results={}
    for name,args in plans.items():
     schema=schemas[name]
     unknown=set(args)-set(schema.get('properties',{}))
     errors=list(Draft202012Validator(schema).iter_errors(args))
     if unknown or errors:raise ValueError((name,unknown,[e.message for e in errors]))
     results[name]={'schema_fields_match':True,'json_schema_valid':True,'invoked':False}
    bad=dict(plans['interface_dispatch'],review=True)
    rejected=sorted(set(bad)-set(schemas['interface_dispatch']['properties']))
    if rejected!=['review']:raise ValueError('original error must be caught')
    compiled=await session.call_tool('interface_validate',{'program':program})
    save('actual-validation.json',compiled.model_dump(mode='json'))
    if compiled.isError:raise ValueError('program rejected by actual static validation')
    save('prospective-plans.json',plans)
    save('result.json',{'status':'PASS_SYNTAX_PREFLIGHT_ONLY','tools':results,
     'original_error_rejected':rejected,'actual_static_validation_invoked':True,
     'input_tools_invoked':False,'native_display_connected':False,
     'provider_conversion':'unverified','scope':'prospective syntax only; leases/review IDs/images/bindings must come from a new live owner'})
asyncio.run(main())
