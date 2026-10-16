// Synthetic host and local file effect; actual exchange/caller, no native input.
import test from 'node:test';
import assert from 'node:assert/strict';
import {appendFile, mkdir, mkdtemp, readFile, readdir, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createPrimaryExchange} from './primary_exchange.mjs';

for (const route of ['guarded-local', 'direct-post']) {
  for (const fault of ['presentation', 'partial-effect']) {
    test(`${route} ${fault} retains one file effect, stops resend, permits explicit close`, async t => {
      const parent = await mkdtemp(join(tmpdir(), 'exchange-effect-'));
      t.after(() => rm(parent, {recursive:true, force:true}));
      const directory = join(parent, 'exchange');
      const effect = join(parent, 'effect.txt');
      await writeFile(effect, '');
      const calls = [];
      const original = {attempt:1,result:{isError:false,content:[{type:'text',text:JSON.stringify({
        status:'completed',image_status:'image',result:{execution:{releases:[
          {verified:true,keys_down:[],buttons_down:[]}
        ]}}
      })}]}};
      const closed = {attempt:2,result:{isError:false,content:[{type:'text',text:'{"status":"closed"}'}]}};
      const host = {sendPresented:async (tool,args) => {
        calls.push({tool,args});
        if (tool === 'interface_close') return closed;
        await appendFile(effect, 'A');
        if (fault === 'partial-effect') throw Error('synthetic host lost reply after file effect');
        return original;
      }};
      const exchange = await createPrimaryExchange({host,directory,route});
      const tool = route === 'guarded-local' ? 'interface_guarded_input' : 'interface_dispatch';
      const args = route === 'guarded-local' ?
        {alias:'save',offset:[1,1],interaction:'click',tail:[]} : {target:'fixture',program:'save'};
      const request = {id:1,method:'call',args:[tool,args]};
      if (fault === 'presentation') await writeFile(join(directory,'presentation-1.json'),'occupied');
      let failure;
      try { await exchange.execute(request); } catch (error) { failure=String(error); }
      const afterFailure=exchange.state();
      let refused;
      try { await exchange.execute({id:2,method:'call',args:[tool,args]}); }
      catch (error) { refused=String(error); }
      const afterRefusal=exchange.state();
      let closeResult,closeError;
      try { closeResult=await exchange.execute({id:2,method:'call',args:['interface_close',{}]}); }
      catch(error) { closeError=String(error); }
      const final=exchange.state();
      const files = {};
      for (const name of await readdir(directory)) files[name]=await readFile(join(directory,name),'utf8');
      const savedEffect=await readFile(effect,'utf8');
      if (process.env.PRIMARY_FAILURE_EVIDENCE) {
        const destination=join(process.env.PRIMARY_FAILURE_EVIDENCE,'exchange-effects',`${route}-${fault}`);
        await mkdir(destination,{recursive:true});
        await writeFile(join(destination,'WITNESS.json'),JSON.stringify({route,fault,request,calls,
          failure,refused,afterFailure,afterRefusal,closeResult,closeError,final,savedEffect,files},null,2)+'\n',{flag:'wx'});
        await writeFile(join(destination,'effect.txt'),savedEffect,{flag:'wx'});
        for (const [name,value] of Object.entries(files)) await writeFile(join(destination,name),value,{flag:'wx'});
      }
      assert.match(failure, fault==='presentation' ? /EEXIST/ : /lost reply/);
      assert.ok(afterFailure.stopped);
      assert.equal(afterFailure.next_id,2);
      assert.match(refused,/exchange stopped/);
      assert.equal(afterRefusal.next_id,2);
      assert.equal(afterRefusal.busy,false);
      assert.equal(savedEffect,'A');
      assert.deepEqual(calls.map(c=>c.tool),[tool,'interface_close']);
      assert.equal(closeError,undefined);
      assert.equal(closeResult.next_id,3);
      assert.equal(final.next_id,3);
      assert.ok(final.stopped);
      assert.deepEqual(JSON.parse(files['request-1.json']),request);
      assert.deepEqual(JSON.parse(files['request-2.json']),{id:2,method:'call',args:['interface_close',{}]});
      assert.deepEqual(JSON.parse(files['original-reply-2.json']),closed);
      if (fault==='presentation') {
        assert.deepEqual(JSON.parse(files['original-reply-1.json']),original);
        assert.equal(files['presentation-1.json'],'occupied');
        assert.equal(afterFailure.caller_state.stopped,null);
      } else {
        assert.equal(files['original-reply-1.json'],undefined);
        assert.equal(files['presentation-1.json'],undefined);
        assert.ok(afterFailure.caller_state.stopped);
      }
    });
  }
}
