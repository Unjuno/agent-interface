import test from 'node:test';
import assert from 'node:assert/strict';
import {appendFileSync} from 'node:fs';
import {createPrimaryCaller} from './primary_caller.mjs';

// Removing any array/type/neutral gate must permit a prohibited later call.
// JSON injection is necessary: conforming backends need not emit these shapes.
const neutral = {verified:true,keys_down:[],buttons_down:[]};
const cases = [
  ['neutral',[neutral],true],
  ['two-neutral',[neutral,neutral],true],
  ['empty-releases',[],false],
  ['string-releases','x',false],
  ['object-releases',{length:1},false],
  ['string-keys',[{verified:true,keys_down:'',buttons_down:[]}],false],
  ['string-buttons',[{verified:true,keys_down:[],buttons_down:''}],false],
  ['object-keys',[{verified:true,keys_down:{length:0},buttons_down:[]}],false],
  ['object-buttons',[{verified:true,keys_down:[],buttons_down:{length:0}}],false],
  ['missing-keys',[{verified:true,buttons_down:[]}],false],
  ['missing-buttons',[{verified:true,keys_down:[]}],false],
  ['null-keys',[{verified:true,keys_down:null,buttons_down:[]}],false],
  ['null-buttons',[{verified:true,keys_down:[],buttons_down:null}],false],
  ['held-key',[{verified:true,keys_down:['Shift'],buttons_down:[]}],false],
  ['held-button',[{verified:true,keys_down:[],buttons_down:['left']}],false],
  ['numeric-verified',[{verified:1,keys_down:[],buttons_down:[]}],false],
  ['false-verified',[{verified:false,keys_down:[],buttons_down:[]}],false],
  ['mixed-unknown',[neutral,{verified:true,keys_down:'',buttons_down:[]}],false],
];

for(const mode of ['guarded-raw','direct-raw','direct-summary'])
  for(const [name,releases,wantContinue] of cases)
    test('typed release '+mode+' '+name+' preserves evidence and enforces continuation',async()=>{
      const route=mode==='guarded-raw'?'guarded-local':'direct-post';
      const tool=mode==='guarded-raw'?'interface_guarded_input':'interface_dispatch';
      const meta=mode==='direct-summary'?{
        schema:'agent-interface/review-v1',image_status:'image',
        receipt:{schema:'agent-interface/receipt-view-dispatch-summary-v1',execution_summary:{releases}},
        outcome_summary:{execution_status:'completed',input_release_verified:true,recovery_required:false,error:null},
      }:{status:'completed',image_status:'image',result:{execution:{releases}}};
      // Force the same JSON boundary used by primary response extraction.
      const original={attempt:1,result:{isError:false,content:[
        {type:'text',text:JSON.stringify(meta)},
        {type:'image',mimeType:'image/png',data:'AAECAw=='},
      ]}};
      const clock={result:{isError:false,content:[{type:'text',text:'{"status":"clock"}'}]}};
      const closed={result:{isError:false,content:[{type:'text',text:'{"status":"closed"}'}]}};
      const submitted=[],shown=[];
      const sinks={text:value=>shown.push({type:'text',value}),image:value=>shown.push({type:'image',value})};
      const host={sendPresented:async(t,args,callbacks)=>{
        submitted.push({tool:t,args:structuredClone(args)});
        const reply=t===tool?original:t==='interface_close'?closed:clock;
        for(const c of reply.result.content) {
          if(c.type==='text')callbacks.text(c.text);else callbacks.image(c);
        }
        return reply;
      }};
      const caller=createPrimaryCaller(host,route,sinks);
      let first,firstError=null,next,nextError=null;
      try{first=await caller.call(tool,{case:name});}catch(error){firstError={name:error.name,message:error.message};}
      const firstStop=caller.state().stopped,firstShown=structuredClone(shown);
      try{next=await caller.call('interface_clock',{});}catch(error){nextError={name:error.name,message:error.message};}
      const close=await caller.call('interface_close',{});
      const row={mode,name,wantContinue,original,firstReturnSame:first===original,firstError,firstStop,
        firstShown,nextError,nextReturnSame:next===clock,closeReturnSame:close===closed,submitted,finalStop:caller.state().stopped};
      if(process.env.TASK_PRIMARY_RELEASE_TRACE)appendFileSync(process.env.TASK_PRIMARY_RELEASE_TRACE,JSON.stringify(row)+'\n');
      assert.equal(firstError,null,'unknown release shape must retain the original response');
      assert.equal(first,original);
      assert.deepEqual(firstShown,[{type:'text',value:original.result.content[0].text},{type:'image',value:original.result.content[1]}]);
      if(wantContinue){assert.equal(firstStop,null);assert.equal(nextError,null);assert.equal(next,clock);}
      else{assert.ok(firstStop);assert.match(nextError?.message??'',/trial stopped/);assert.equal(submitted.filter(x=>x.tool==='interface_clock').length,0);}
      assert.equal(close,closed);
      assert.deepEqual(submitted.map(x=>x.tool),wantContinue?[tool,'interface_clock','interface_close']:[tool,'interface_close']);
    });
