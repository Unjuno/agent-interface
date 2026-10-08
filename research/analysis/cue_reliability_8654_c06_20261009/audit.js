// Independent raw-only audit for Issue #8654 C06.
"use strict";
function auditC06(files, skipMutations=false) {
  const regimes=["STABLE","REVERSAL","GLOBAL_SHIFT"];
  const D=(4n**8n)*(20n**8n);
  function qNum(r,c,a) {
    const aligned=(a===c);
    if(r==="STABLE") return aligned?16:4;
    if(r==="REVERSAL") return aligned?4:16;
    if(r==="GLOBAL_SHIFT") return aligned?11:3;
    throw Error("regime");
  }
  const seen=new Set(), mass={}, htNumer={}, oracleNum={STABLE:160,REVERSAL:160,GLOBAL_SHIFT:112};
  const errors={}; let rows=0, identified=0, greedyUnident=0;
  let absError={STABLE:0,REVERSAL:0,GLOBAL_SHIFT:0}, maxError={STABLE:0,REVERSAL:0,GLOBAL_SHIFT:0};
  for(const [path,content] of Object.entries(files)) {
    const lines=content.trimEnd().split("\n");
    for(const line of lines) {
      const p=line.split("|");
      if(p.length!==5) throw Error("schema");
      const [r,policy,ah,yh,ns]=p;
      if(!regimes.includes(r)||!["D","G"].includes(policy)||!/^[0-9a-f]{2}$/.test(ah)||!/^[0-9a-f]{2}$/.test(yh)||!/^[0-9]+$/.test(ns)) throw Error("encoding");
      const am=parseInt(ah,16), ym=parseInt(yh,16), n=BigInt(ns);
      const expectedPath="raw/"+r.toLowerCase()+"_"+(policy==="D"?"diagnostic_"+Math.floor(am/64):"greedy")+".jsonl";
      if(path!==expectedPath||(policy==="G"&&am!==0)) throw Error("path_or_policy");
      const key=r+"|"+policy+"|"+ah+"|"+yh;
      if(seen.has(key)) throw Error("duplicate"); seen.add(key);
      let exp=1n, cells=new Set(), hnum=0;
      for(let i=0;i<8;i++) {
        const c=Math.floor(i/4), flip=policy==="D"?((am>>i)&1):0;
        const y=(ym>>i)&1, a=flip?1-c:c, q=qNum(r,c,a);
        exp*=BigInt(policy==="D"?(flip?1:3):4)*BigInt(y?q:20-q);
        if(y) hnum+=policy==="D"?(flip?3:1):0;
        cells.add(c+"|"+a);
      }
      if(n!==exp) throw Error("weight");
      const expectedCount=policy==="D"?65536:256;
      mass[r+"|"+policy]=(mass[r+"|"+policy]||0n)+n;
      htNumer[r+"|"+policy]=(htNumer[r+"|"+policy]||0n)+n*BigInt(hnum);
      rows++;
      const isIdentified=cells.size===4;
      if(policy==="G"&&!isIdentified) greedyUnident++;
      if(policy==="D"&&isIdentified) identified+=Number(n);
      if(policy==="D") {
        const est=hnum/12, target=oracleNum[r]/320, e=Math.abs(est-target);
        absError[r]+=Number(n)/Number(D)*e;
        maxError[r]=Math.max(maxError[r],e);
      }
    }
  }
  for(const r of regimes) for(const policy of ["D","G"]) {
    const key=r+"|"+policy, required=policy==="D"?65536:256;
    const count=[...seen].filter(x=>x.startsWith(key+"|")).length;
    if(count!==required||mass[key]!==D) throw Error("coverage_or_mass:"+key);
    if(policy==="D"&&htNumer[key]*320n!==D*12n*BigInt(oracleNum[r])) throw Error("ips_expectation:"+key);
  }
  if(rows!==197376||seen.size!==197376||greedyUnident!==768) throw Error("total_or_greedy");
  let mutationsRejected=0;
  if(!skipMutations) {
    const path=Object.keys(files).sort()[0];
    const mutations=[
      copy=>{const a=copy[path].trimEnd().split("\\n");a.pop();copy[path]=a.join("\\n")+"\\n";},
      copy=>{const a=copy[path].trimEnd().split("\\n");a[1]=a[0];copy[path]=a.join("\\n")+"\\n";},
      copy=>{const a=copy[path].trimEnd().split("\\n");const p=a[0].split("|");p[4]=(BigInt(p[4])+1n).toString();a[0]=p.join("|");copy[path]=a.join("\\n")+"\\n";},
      copy=>{const a=copy[path].trimEnd().split("\\n");a[0]+="|oracle";copy[path]=a.join("\\n")+"\\n";}
    ];
    for(const mutate of mutations){const copy={...files};mutate(copy);try{auditC06(copy,true)}catch{mutationsRejected++}}
    if(mutationsRejected!==4) throw Error("mutation_controls");
  }
  return {rows,unique:seen.size,mutations_rejected:mutationsRejected,groups:Object.fromEntries(Object.entries(mass).map(([k,v])=>[k,v===D?"unit_mass":"bad"])),
    diagnostic_identified_probability_by_regime:Object.fromEntries(regimes.map(r=>[r,Number(identified)/3/Number(D)])),
    exact_known_propensity_expectation:true,greedy_unidentifiable_rows:greedyUnident,
    diagnostic_expected_absolute_error:absError,diagnostic_max_absolute_error:maxError};
}
if(typeof module!=="undefined") module.exports=auditC06;
