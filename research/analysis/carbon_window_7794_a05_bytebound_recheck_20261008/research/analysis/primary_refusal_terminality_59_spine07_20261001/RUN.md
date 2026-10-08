# Executed runner

Exactly one Node process was run from the temporary checkout root, with the candidate imported from `./spine07-primary-policy.mjs`. The command used was:

```sh
node --input-type=module -e 'import {createPrimaryTrialCaller} from "./spine07-primary-policy.mjs"; let calls=0; const host={sendPresented:async()=>{calls++; if(calls===1) return {}; return {result:{isError:false,content:[{type:"text",text:JSON.stringify({status:"completed",result:{execution:{releases:[{verified:true,keys_down:[],buttons_down:[]}]}}})}]}}}}; const caller=createPrimaryTrialCaller(host,"direct",{}); let firstError=""; try { await caller.call("interface_dispatch",{program:{}}); } catch(e) { firstError=String(e); } const stoppedAfterMalformed=caller.state().stopped; let secondStatus=""; try { const r=await caller.call("interface_dispatch",{program:{}}); secondStatus=r.result.content[0].text; } catch(e) { secondStatus="THREW:"+String(e); } console.log(JSON.stringify({candidate_sha:"b2f27b6cda362db24e906090f33c4813d60f2867",candidate_invocations:2,firstError,stoppedAfterMalformed,secondCall:secondStatus,callsAtHost:calls,finalStopped:caller.state().stopped},null,2));'
```

The command's structured stdout is preserved in `RAW.json`. `candidate_invocations` in that stdout counts the two caller attempts inside this single process; it is not two process runs.
