const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const w=JSON.parse(fs.readFileSync(path.join(__dirname,'../workflows/oke-index.json')));
const node=name=>w.nodes.find(n=>n.name===name);
const run=input=>vm.runInNewContext(`(function(){${node('색인 결과 검증').parameters.jsCode}})()`,{$input:{first:()=>({json:input})}})[0].json;
test('inactive index workflow uses authenticated HTTP and valid graph',()=>{
  assert.equal(w.active,false);
  assert.equal(w.meta.realIndexingVerified,false);
  assert.equal(w.nodes.length,3);
  assert.equal(w.nodes.some(n=>n.type==='n8n-nodes-base.executeCommand'),false);
  const http=node('실제 색인 서비스 호출');
  assert.match(http.parameters.url,/INDEX_SERVICE_URL/);
  assert.equal(http.parameters.genericAuthType,'httpHeaderAuth');
  const names=new Set(w.nodes.map(n=>n.name));
  for(const [source,links] of Object.entries(w.connections)) {
    assert.equal(names.has(source),true);
    for(const group of links.main) for(const edge of group) assert.equal(names.has(edge.node),true);
  }
});
test('index result accepts eight successful documents and rejects errors',()=>{
  const documents=Array.from({length:8},(_,i)=>({doc_key:'doc'+i,status:'indexed',chunk_count:1,reason:null}));
  const body={ok:true,mode:'postgres_unverified',counts:{indexed:8,skipped:0,rejected:0,failed:0},documents};
  assert.equal(run({statusCode:200,body}).ok,true);
  assert.equal(run({statusCode:503,body}).ok,false);
  assert.equal(run({error:'private'}).reason,'index_unavailable');
  assert.equal(run({statusCode:200,body:{...body,counts:{...body.counts,failed:1}}}).ok,false);
});
