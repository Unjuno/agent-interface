// Issue #8654 C06: exhaustive stochastic-outcome support enumeration.
"use strict";
function enumerateC06() {
  const regimes=["STABLE","REVERSAL","GLOBAL_SHIFT"];
  const denominator=(4n**8n)*(20n**8n);
  const files={};
  function qNum(regime,c,a) {
    const aligned=(a===c);
    if(regime==="STABLE") return aligned?16:4;
    if(regime==="REVERSAL") return aligned?4:16;
    return aligned?11:3;
  }
  function hex(v){return v.toString(16).padStart(2,"0");}
  for(const regime of regimes) {
    for(let shard=0;shard<4;shard++) {
      const lines=[];
      for(let am=shard*64;am<(shard+1)*64;am++) {
        for(let ym=0;ym<256;ym++) {
          let n=1n;
          for(let i=0;i<8;i++) {
            const c=Math.floor(i/4), flip=(am>>i)&1, y=(ym>>i)&1;
            const a=flip?1-c:c, q=qNum(regime,c,a);
            n*=BigInt(flip?1:3)*BigInt(y?q:20-q);
          }
          lines.push(regime+"|D|"+hex(am)+"|"+hex(ym)+"|"+n.toString());
        }
      }
      files["raw/"+regime.toLowerCase()+"_diagnostic_"+shard+".jsonl"]=lines.join("\n")+"\n";
    }
    const lines=[];
    for(let ym=0;ym<256;ym++) {
      let n=4n**8n;
      for(let i=0;i<8;i++) {
        const c=Math.floor(i/4), y=(ym>>i)&1, q=qNum(regime,c,c);
        n*=BigInt(y?q:20-q);
      }
      lines.push(regime+"|G|00|"+hex(ym)+"|"+n.toString());
    }
    files["raw/"+regime.toLowerCase()+"_greedy.jsonl"]=lines.join("\n")+"\n";
  }
  return {files,denominator:denominator.toString()};
}
if(typeof module!=="undefined") module.exports=enumerateC06;
