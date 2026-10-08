import assert from 'node:assert/strict';
import {createPrimaryTrialCaller} from './primary-policy.mjs';
const args={alias:'layout_probe_a',offset:[12,19],interaction:'click',tail:[],detail:'brief',observation_refs:true};
const expectation={id:'layout-mismatch',tool:'interface_guarded_input',args,kind:'guard',reason:'region_pixels_missing',revision:0,alias:'layout_probe_a'};
const meta={status:'refused',replay_allowed:false,result:{input_dispatched:false,guard_checks:[{stage:'before_admission',status:'MISSING',reason:'region_pixels_missing',handle:'layout_probe_a'}]},session:{binding_revision:0,recovery_required:false}};
const reply={result:{isError:true,content:[{type:'text',text:JSON.stringify(meta)},{type:'image',data:'original'}]}};
function setup(r=reply,expected=[expectation]){const calls=[];return {calls,caller:createPrimaryTrialCaller({sendPresented:async(tool,args)=>{calls.push({tool,args});return r;},review:async()=>{}},'guarded-local',{},expected)};}
{
 const {caller,calls}=setup();assert.equal(await caller.call(expectation.tool,args,'layout-mismatch'),reply);
 assert.equal(caller.state().stopped,null,'exact declared no-input refusal must not stop');
 await assert.rejects(caller.call(expectation.tool,args,'layout-mismatch'),/control already consumed/);assert.equal(calls.length,1);
}
{
 const {caller,calls}=setup();await assert.rejects(caller.call(expectation.tool,{...args,alias:'other'},'layout-mismatch'),/control request mismatch/);assert.equal(calls.length,0);
}
for(const change of [m=>m.result.guard_checks[0].status='STALE',m=>m.result.input_dispatched=true,m=>m.session.recovery_required=true,m=>m.session.binding_revision=1]){
 const changed=structuredClone(meta);change(changed);const r={result:{isError:true,content:[{type:'text',text:JSON.stringify(changed)}]}};
 const {caller}=setup(r);assert.equal(await caller.call(expectation.tool,args,'layout-mismatch'),r);assert.ok(caller.state().stopped);
}
{
 const {caller}=setup();assert.equal(await caller.call(expectation.tool,args),reply);assert.ok(caller.state().stopped);
}
const mintArgs={alias:'old_source_control',source_sequence:4,point:[230,401],region_size:[24,38]};
const mintExpectation={id:'revoked-source',tool:'interface_guarded_mint',args:mintArgs,kind:'source',error:'KeyError(4)',revision:1};
{
 const r={result:{isError:true,content:[{type:'text',text:JSON.stringify({status:'refused',replay_allowed:false,input_dispatched:false,error:'KeyError(4)',session:{binding_revision:1,recovery_required:false}})}]}};
 const {caller}=setup(r,[mintExpectation]);assert.equal(await caller.call(mintExpectation.tool,mintArgs,mintExpectation.id),r);assert.equal(caller.state().stopped,null);
}
console.log('PASS explicit one-shot controls, exact request, STALE/input/recovery/revision mismatch STOP, ordinary refusal STOP and revoked source');
