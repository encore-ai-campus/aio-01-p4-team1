#!/usr/bin/env python3
"""Read only per-node timing for listed request IDs from the team's n8n SQLite DB."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
from live_check import load_settings, local_commit
from vm_access import VMTerminal


async def profile(settings, request_ids):
    script = r'''
const {DatabaseSync}=require('node:sqlite');
const db=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});
function decode(serialized){
 const input=JSON.parse(serialized);
 if(!Array.isArray(input))return input;
 const output=input.map(x=>Array.isArray(x)?[]:x&&typeof x==='object'?{}:x);
 for(let i=0;i<input.length;i++){
  if(!input[i]||typeof input[i]!=='object')continue;
  for(const key of Object.keys(input[i])){
   const value=input[i][key];
   if(typeof value==='string'&&!/^\d+$/.test(value))throw Error('unexpected serialization');
   output[i][key]=typeof value==='string'?output[Number(value)]:value;
  }
 }
 return output[0];
}
const ids=REQUEST_IDS;
const rows=db.prepare('SELECT e.id,e.startedAt,e.stoppedAt,e.status,x.data FROM execution_entity e JOIN execution_data x ON x.executionId=e.id WHERE e.workflowId=? ORDER BY e.id DESC LIMIT 100').all('okeSupportFlow01');
const result=[];
for(const row of rows){
 const rid=ids.find(x=>row.data.includes(x));
 if(!rid)continue;
 const runs=decode(row.data).resultData.runData;
 result.push({request_id:rid,execution_id:row.id,started_at:row.startedAt,stopped_at:row.stoppedAt,status:row.status,
  nodes:Object.entries(runs).map(([name,items])=>({name,durations_ms:items.map(x=>x.executionTime)}))});
}
db.close();console.log(JSON.stringify(result));
'''.replace('REQUEST_IDS', json.dumps(request_ids))
    async with VMTerminal(settings.get('VM_WEB_URL', 'https://aio-t1.isitsoft.kr/ssh/'),
                          settings.get('VM_USER', 'toor'), settings['VM_PASSWORD']) as terminal:
        status, output = await terminal.run('docker exec oke-n8n-1 node -e ' + shlex.quote(script))
    if status:
        raise RuntimeError('profile read failed')
    return json.loads(output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file')
    parser.add_argument('--input', action='append', required=True, help='sanitized latency report, repeat for before/after')
    parser.add_argument('--output', required=True)
    args=parser.parse_args()
    output=Path(args.output)
    if output.exists(): parser.error('output already exists')
    settings=load_settings(args.env_file)
    if not settings.get('VM_PASSWORD'): parser.error('missing VM_PASSWORD')
    ids=[]
    for name in args.input:
        data=json.loads(Path(name).read_text())
        ids.extend(r['request_id'] for r in data['records'])
    if not ids or any(not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',rid) for rid in ids):
        parser.error('input requires safe request IDs')
    report={'schema':'oke-node-timing-v1','observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'read-only n8n node timings, no inputs, answers or credentials',
        'runner_source_commit':local_commit(),'executions':[],'errors':[]}
    try:
        report['executions']=asyncio.run(profile(settings,ids))
        seen={r['request_id'] for r in report['executions']}
        report['missing_request_ids']=sorted(set(ids)-seen)
    except Exception as error:
        report['errors'].append(type(error).__name__)
        report['missing_request_ids']=ids
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2); stream.write('\n')
    print(json.dumps({'executions':len(report['executions']),'missing':len(report['missing_request_ids']),'errors':report['errors']}))
    return 1 if report['errors'] or report['missing_request_ids'] else 0


if __name__=='__main__':
    raise SystemExit(main())
