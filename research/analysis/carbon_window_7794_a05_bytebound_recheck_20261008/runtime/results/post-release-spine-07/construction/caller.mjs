export const meta=r=>JSON.parse(r.result.content.find(x=>x.type==='text').text);
export const nav=url=>[{op:'key_chord',keys:['CTRL','l']},{op:'wait_update',timeout_ms:100},{op:'text',text:url},{op:'wait_update',timeout_ms:100},{op:'key_chord',keys:['ENTER']},{op:'wait_update',timeout_ms:200}];
export const field=token=>[{op:'key_chord',keys:['CTRL','a']},{op:'wait_update',timeout_ms:100},{op:'text',text:token},{op:'wait_update',timeout_ms:100}];
export const move=p=>({op:'pointer_move',frame:'screen_physical_px',x:p[0],y:p[1]});
const press=[{op:'pointer_button',button:'left',down:true},{op:'pointer_button',button:'left',down:false}];
export const batch=(token,a,b)=>[move(a),...press,...field(token),move(b),{op:'wait_update',timeout_ms:100},...press,{op:'wait_update',timeout_ms:100}];
export const program=(seq,id,expiry,ops)=>({schema:'agent-interface/program-v1',program_id:id,source:{observation_seq:seq,binding_revision:1},authority:{lease_id:'spine07-direct',expires_at_ns:expiry},terminal:{release_all_required:true},ops:[{op:'focus',target:'browser'},...ops,{op:'release_all'}]});
import {createPrimaryTrialCaller} from './primary-policy.mjs';
export async function open(ctx,route,sinks){
 const root=ctx.root+'/'+route+'/session', allocation=JSON.parse(await ctx.fs.readFile(root+'/allocation.json','utf8')),goal=JSON.parse(await ctx.fs.readFile(root+'/goal.json','utf8'));
 if(allocation.source!==ctx.source||allocation.seed!==ctx.seed)throw Error('allocation drift');
 const directory=ctx.parent+'/post-release-spine-07-'+route+'-host';
 const factory=(await import(ctx.url.pathToFileURL(ctx.root+'/host-bundle/relay_host.mjs').href)).createInstrumentedRelayClient;
 const host=await factory({command:'wsl.exe',args:['-d','Ubuntu','-u','taka','--exec','/tmp/agent-interface-mcp-venv/bin/python',ctx.linux+'/runtime.pyz','relay','--','--targets',ctx.linux+'/'+route+'/session/targets.json','--output-directory',ctx.linux+'/'+route+'/session/server','--session-mode',route==='guarded-local'?'guarded-x11':'persistent-x11','--display',allocation.display],evidenceDirectory:directory,reuseReviewedImages:false});
 let seq=1,n=0;
 const controls=route==='guarded-local' ? ctx.controls : [];
 const policy=createPrimaryTrialCaller(host,route,sinks,controls);
 const call=policy.call;

 return {route,allocation,goal,directory,host,call,review:policy.review,acknowledgeText:policy.acknowledgeText,state:policy.state,
 input:async(args,controlId=null)=>call('interface_guarded_input',{detail:'brief',observation_refs:true,...args},controlId),
 direct:async(phase,ops)=>{const c=meta(await call('interface_clock',{}));if(c.authority_granted!==false||c.lease_issued!==false||!Number.isSafeInteger(c.monotonic_ns))throw Error('clock');const r=await call('interface_dispatch',{program:program(seq,'spine07-'+phase+'-'+(++n),c.monotonic_ns+5000000000,ops),current_observation_seq:seq,current_binding_revision:1,compact:true,report_refs:true,detail:'summary',inspect_after:'browser',inspect_after_region:[0,0,1280,800]});seq++;return r;},
 preflight:async()=>{for(const [i,ops] of [nav(goal.tasks[0].url),batch(goal.tasks[0].token,[230,401],[376,401]),batch(goal.tasks[3].token,[630,558],[689,634])].entries()){const r=await call('interface_validate',{program:program(1,'spine07-preflight-'+i,5000000000,ops)});if(meta(r).status!=='valid')throw Error('preflight');}},
 initial:()=>call(route==='guarded-local'?'interface_guarded_observe':'interface_observe',route==='guarded-local'?{}:{target:'browser',frame:'screen_physical_px',region:[0,0,1280,800],compact:true,report_refs:true}),
 close:()=>call('interface_close',{})};
}