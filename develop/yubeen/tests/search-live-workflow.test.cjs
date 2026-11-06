const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const w=JSON.parse(fs.readFileSync(path.join(__dirname,'../workflows/oke-search.json')));
const node=name=>w.nodes.find(n=>n.name===name);
const run=(name,input)=>vm.runInNewContext(`(function(){${node(name).parameters.jsCode}})()`,{$input:{first:()=>({json:input})}})[0].json;
test('live workflow remains inactive and has no synthetic search',()=>{
  assert.equal(w.active,false);
  assert.equal(w.meta.realSearchVerified,false);
  assert.equal(w.nodes.filter(n=>n.type==='n8n-nodes-base.httpRequest').length,1);
  assert.equal(w.nodes.some(n=>n.type==='n8n-nodes-base.executeCommand'),false);
  assert.match(node('실제 검색 서비스 호출').parameters.url,/SEARCH_SERVICE_URL/);
  const names=new Set(w.nodes.map(n=>n.name));
  for(const [source,links] of Object.entries(w.connections)) {
    assert.equal(names.has(source),true);
    for(const group of links.main) for(const edge of group) assert.equal(names.has(edge.node),true);
  }
});
test('IT body is forwarded only for independent service authorization',()=>{
  const req={body:{request_id:'r',query:'vpn',type:'network',access_levels:['all','it'],top_k:3,role:'admin'}};
  assert.equal(run('요청 형식 확인',req).valid,true);
  assert.equal(run('요청 형식 확인',req).request.access_levels[1],'it');
  req.body.access_levels=['all'];
  assert.equal(run('요청 형식 확인',req).valid,true);
  assert.equal(run('요청 형식 확인',req).request.access_levels[0],'all');
});
test('live response normalization preserves C03 and hides errors',()=>{
  const normal=run('검색 응답 검증',{statusCode:200,body:{ok:true,evidence:[],reason:'no_evidence'}});
  assert.equal(normal.status,200);
  assert.equal(normal.body.reason,'no_evidence');
  const error=run('검색 응답 검증',{error:'private',statusCode:503});
  assert.equal(error.status,503);
  assert.equal(error.body.reason,'search_unavailable');
  for (const [status,reason] of [[400,'invalid_request'],[401,'unauthorized'],[403,'forbidden']]) {
    const result=run('검색 응답 검증',{statusCode:status,body:{private:'hidden'}});
    assert.equal(result.status,status);
    assert.equal(result.body.reason,reason);
    assert.equal(result.body.private,undefined);
  }
});
