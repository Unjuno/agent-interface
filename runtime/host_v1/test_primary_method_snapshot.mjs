import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';
function fixture(){const calls=[];const c=createPrimaryCaller({async sendPresented(tool,args){calls.push({tool,args});const meta=tool==='interface_guarded_mint_many'?{status:'minted',source_sequence:1,minted:[{alias:'note'}]}:tool==='interface_guarded_input'?{status:'completed',image_status:'image',result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}},...(args.feedback?{feedback:{status:'matched',expected_title:'Saved',rejected_titles:[],title:'Saved',after_title:'Saved',task_success:null,authority_granted:false,input_dispatched:false}}:{})}:{status:'minted'};return {result:{isError:false,content:[{type:'text',text:JSON.stringify(meta)}]}};}},'guarded-local',{text(){},image(){}});return {c,calls};}
function parameters(method,a=[20,30]){return method==='mint'?['note',1,a,[24,38]]:method==='mintMany'?[1,[{alias:'note',point:a,region_size:[24,38]}]]:method==='inputWithFeedback'?['note',a,'click',[],{expected_title:'Saved'}]:['note',a,'click',[]];}
for(const method of ['input','inputWithFeedback','mint','mintMany']){
 for(const fault of ['proxy','getter','function'])test('primary method snapshot '+method+' '+fault,async()=>{
  const {c,calls}=fixture();let a=[20,30];if(fault==='proxy')a=new Proxy(a,{});if(fault==='getter')Object.defineProperty(a,'0',{enumerable:true,get(){throw Error('getter fault');}});if(fault==='function')a[0]=()=>1;
  await assert.rejects(c[method](...parameters(method,a)));assert.equal(c.state().stopped,'primary method argument snapshot failure');
  await assert.rejects(c.call('interface_clock',{}),/trial stopped/);await c.call('interface_close',{});assert.deepEqual(calls.map(x=>x.tool),['interface_close']);
 });
 test('primary method snapshot healthy '+method,async()=>{const {c,calls}=fixture();await c[method](...parameters(method));assert.equal(c.state().stopped,null);assert.equal(calls.length,1);});
}
for(const method of ['mint','mintMany','input'])test('primary method snapshot indexed iterator '+method,async()=>{
 const {c,calls}=fixture();const a=[20,30];a[Symbol.iterator]=function*(){yield NaN;yield NaN;};await c[method](...parameters(method,a));
 const args=calls[0].args;assert.deepEqual(method==='mint'?args.point:method==='mintMany'?args.references[0].point:args.offset,[20,30]);assert.equal(c.state().stopped,null);
});
test('primary method snapshot rejects hidden invalid batch indexes',async()=>{const {c,calls}=fixture();const a=[NaN,30];a[Symbol.iterator]=function*(){yield 20;yield 30;};await assert.rejects(c.mintMany(1,[{alias:'note',point:a,region_size:[24,38]}]),/invalid primary batch/);assert.equal(calls.length,0);});
test('primary method snapshot stopped caller never evaluates new getter',async()=>{const {c,calls}=fixture();await assert.rejects(c.call('unavailable',{}));let reads=0;const a=[20,30];Object.defineProperty(a,'0',{enumerable:true,get(){reads++;return 20;}});await assert.rejects(c.mint(...parameters('mint',a)),/trial stopped/);assert.equal(reads,0);assert.equal(calls.length,0);});
