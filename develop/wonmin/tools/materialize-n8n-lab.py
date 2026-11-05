#!/usr/bin/env python3
"""Generate private lab deployment copies; original workflow JSON stays unchanged."""
from pathlib import Path
import copy
import json
import secrets
import uuid

OWN = Path(__file__).resolve().parents[1]


def main():
    runtime = OWN / '.runtime'
    idsfile = runtime / 'workflow-ids.json'
    if idsfile.exists():
        ids = json.loads(idsfile.read_text())
    else:
        ids = {name: 'wm' + name[:3] + secrets.token_hex(5) for name in ('errors', 'handoff', 'failure', 'llm')}
        idsfile.write_text(json.dumps(ids, indent=2) + '\n')
    credentials = {'WONMIN_APP_STORE_AUTH': 'wonminLabStoreApp',
                   'WONMIN_PRACTICE_STORE_AUTH': 'wonminLabStorePractice', 'WONMIN_X_TEAM_KEY': 'wonminLabTeam'}
    workflows = []
    for name, file in [('errors', 'oke-errors.json'), ('handoff', 'oke-handoff.json')]:
        wf = json.loads((OWN / 'workflows' / file).read_text())
        wf['id'] = ids[name]
        for node in wf['nodes']:
            auth = node.get('credentials', {}).get('httpHeaderAuth')
            if auth:
                auth['id'] = credentials[auth['name']]
        if name == 'errors':
            # Controlled non-sensitive lab executions only; no full exports enter committed reports.
            wf['settings'].update(saveDataErrorExecution='all', saveDataSuccessExecution='all')
        else:
            wf['settings']['errorWorkflow'] = ids['errors']
        workflows.append(wf)
    failure = copy.deepcopy(workflows[1])
    failure['id'] = ids['failure']
    failure['settings'].update(saveDataErrorExecution='all', saveDataSuccessExecution='all')
    for node in failure['nodes']:
        if node['name'] == 'H01 Handoff Webhook':
            node['webhookId'] = str(uuid.uuid5(uuid.NAMESPACE_URL, ids['failure']))
            node['parameters'].update(path='wonmin-p13-failure', authentication='none')
            node.pop('credentials', None)
        elif node['name'] == 'H03 Select Store':
            node['parameters']['jsCode'] = "throw new Error('wonmin-p13-controlled-error');"
    workflows.append(failure)
    llm = {
        'id': ids['llm'], 'name': 'wonmin-local-llm-probe', 'active': False,
        'nodes': [
            {'id': 'llm-webhook', 'webhookId': str(uuid.uuid5(uuid.NAMESPACE_URL, ids['llm'])), 'name': 'Local LLM Webhook', 'type': 'n8n-nodes-base.webhook', 'typeVersion': 2,
             'position': [0, 300], 'parameters': {'httpMethod': 'POST', 'path': 'wonmin-local-llm', 'responseMode': 'responseNode', 'options': {}}},
            {'id': 'llm-call', 'name': 'Call Local Ollama', 'type': 'n8n-nodes-base.httpRequest', 'typeVersion': 4.2,
             'position': [240, 300], 'parameters': {'method': 'POST', 'url': '={{ $env.LOCAL_LLM_BASE_URL + "/api/chat" }}',
               'sendBody': True, 'specifyBody': 'json',
               'jsonBody': '={{ JSON.stringify({model:$env.LOCAL_LLM_MODEL,messages:[{role:"user",content:"Reply with the word OK."}],stream:false,options:{temperature:0,num_predict:8} }) }}',
               'options': {'timeout': 120000, 'response': {'response': {'fullResponse': True, 'neverError': True, 'responseFormat': 'json'}}}}},
            {'id': 'llm-result', 'name': 'Safe Local Result', 'type': 'n8n-nodes-base.code', 'typeVersion': 2,
             'position': [480, 300], 'parameters': {'jsCode': "const r=$input.first().json;return [{json:{ok:r.statusCode===200,model:r.body?.model??null,content:r.body?.message?.content??null,done:r.body?.done===true}}];"}},
            {'id': 'llm-response', 'name': 'Local LLM Response', 'type': 'n8n-nodes-base.respondToWebhook', 'typeVersion': 1.4,
             'position': [720, 300], 'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {'responseCode': 200}}},
        ],
        'connections': {},
        'settings': {'executionOrder': 'v1', 'errorWorkflow': ids['errors'], 'saveDataErrorExecution': 'none', 'saveDataSuccessExecution': 'none'},
    }
    for first, second in [('Local LLM Webhook', 'Call Local Ollama'), ('Call Local Ollama', 'Safe Local Result'), ('Safe Local Result', 'Local LLM Response')]:
        llm['connections'][first] = {'main': [[{'node': second, 'type': 'main', 'index': 0}]]}
    workflows.append(llm)
    target = runtime / 'n8n-import' / 'workflows.json'
    target.write_text(json.dumps(workflows, ensure_ascii=False, indent=2) + '\n')
    target.chmod(0o600)
    print(json.dumps({'deployment_copies': len(workflows), 'original_sources_unchanged': True}))


if __name__ == '__main__':
    main()
