#!/usr/bin/env python3
"""Build private deployment copies from the three already-merged teammate commits."""
import hashlib
import io
import json
from pathlib import Path
import secrets
import subprocess
import tarfile
import uuid

OWN = Path(__file__).resolve().parents[1]
ROOT = OWN.parents[1]
SOURCES = {'jihye': '1902a2b14d6d3a21f80519ffe4a91565b26abb4c',
           'yubeen': '95ef45f5914b5f2e35e7bd8d94b4f94281d5df49',
           'dahyeok': 'b9752869ae62d8a12b1395110d21ff68a4388181'}


def main():
    runtime = OWN / '.runtime'
    manifest = {'sources': SOURCES, 'workflows': [], 'mode': 'private Ubuntu lab'}
    for commit in SOURCES.values():
        subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=ROOT, check=True)
    for owner in ('jihye', 'yubeen'):
        commit = SOURCES[owner]
        target = runtime / ('peer-' + owner + '-' + commit[:7])
        marker = target / '.deployment-source.json'
        if marker.exists():
            assert json.loads(marker.read_text())['commit'] == commit
        else:
            assert not target.exists(), 'do not overwrite an unknown deployment snapshot'
            data = subprocess.check_output(['git', 'archive', commit, 'develop/' + owner], cwd=ROOT)
            target.mkdir(mode=0o700)
            with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                for member in archive.getmembers():
                    path = Path(member.name)
                    if not path.is_relative_to('develop/' + owner):
                        continue
                    relative = path.relative_to('develop/' + owner)
                    if not relative.parts:
                        continue
                    member.name = str(relative)
                    archive.extract(member, target, filter='data')
            marker.write_text(json.dumps({'commit': commit}))

    idsfile = runtime / 'workflow-ids.json'
    ids = json.loads(idsfile.read_text())
    for name in ('support', 'search', 'index'):
        ids.setdefault(name, 'wm' + name[:3] + secrets.token_hex(5))
    idsfile.write_text(json.dumps(ids, indent=2) + '\n')
    specs = [('support', ROOT / 'develop/dahyeok/workflows/oke-support-13.json'),
             ('search', ROOT / 'develop/yubeen/workflows/oke-search.json'),
             ('index', ROOT / 'develop/yubeen/workflows/oke-index.json'),
             ('handoff', OWN / 'workflows/oke-handoff.json'),
             ('errors', OWN / 'workflows/oke-errors.json')]
    credentials = {'LOCAL_X_TEAM_KEY_HEADER_AUTH': 'wonminLabTeam',
                   'SUPPORT_X_TEAM_KEY': 'wonminLabTeam',
                   'SUPPORT_DATA_API_X_API_KEY': 'wonminLabDataApi',
                   'WONMIN_X_TEAM_KEY': 'wonminLabTeam',
                   'WONMIN_APP_STORE_AUTH': 'wonminLabStoreApp',
                   'WONMIN_PRACTICE_STORE_AUTH': 'wonminLabStorePractice'}
    workflows = []
    for name, source in specs:
        owner = {'support': 'dahyeok', 'search': 'yubeen', 'index': 'yubeen'}.get(name)
        source_commit = SOURCES[owner] if owner else None
        # Read the pinned blob itself: dirty/newer working files must not be labelled with an older commit.
        content = (subprocess.check_output(['git', 'show', f'{source_commit}:{source.relative_to(ROOT)}'], cwd=ROOT)
                   if source_commit else source.read_bytes())
        workflow = json.loads(content)
        workflow['id'] = ids[name]
        workflow['active'] = False
        workflow.setdefault('settings', {}).update(saveDataErrorExecution='none', saveDataSuccessExecution='none',
                                                   saveManualExecutions=False, errorWorkflow='' if name == 'errors' else ids['errors'])
        if name == 'index':
            # Only this pinned synthetic Mock workflow contains no inbound headers or real source text.
            command = next(n for n in workflow['nodes'] if n['type'] == 'n8n-nodes-base.executeCommand')['parameters']['command']
            assert '--source mock' in command
            workflow['settings'].update(saveManualExecutions=True, saveDataSuccessExecution='all', saveDataErrorExecution='all')
        for node in workflow['nodes']:
            for kind, auth in node.get('credentials', {}).items():
                auth['id'] = 'wonminLabOllama' if kind == 'openAiApi' else credentials[auth['name']]
            if node['type'].endswith('.lmChatOpenAi'):
                node['parameters']['model'] = {'__rl': True, 'mode': 'id', 'value': 'qwen2.5-coder:latest'}
            if node['type'] == 'n8n-nodes-base.webhook':
                node['webhookId'] = str(uuid.uuid5(uuid.NAMESPACE_URL, ids[name]))
                node['credentials'] = {'httpHeaderAuth': {'id': 'wonminLabTeam', 'name': 'WONMIN_X_TEAM_KEY'}}
            if name == 'search' and node['type'] == 'n8n-nodes-base.httpRequest':
                node['credentials'] = {'httpHeaderAuth': {'id': 'wonminLabTeam', 'name': 'WONMIN_X_TEAM_KEY'}}
        workflow['meta'] = {**workflow.get('meta', {}), 'wonminLabDeployment': True,
                            'sourceSha256': hashlib.sha256(content).hexdigest(), 'sourceCommit': source_commit}
        workflows.append(workflow)
        manifest['workflows'].append({'id': ids[name], 'name': workflow['name'],
                                      'source': str(source.relative_to(ROOT)), 'source_sha256': hashlib.sha256(content).hexdigest(),
                                      'source_commit': source_commit, 'source_kind': 'git_blob' if source_commit else 'working_tree'})
    imports = runtime / 'n8n-import'
    private_values = dict(line.split('=', 1) for line in (runtime / 'lab.env').read_text().splitlines() if '=' in line)
    for path, data in [(imports / 'team-workflows.json', workflows),
                       (imports / 'team-credentials.json', [{'id': 'wonminLabOllama', 'name': 'WONMIN_LOCAL_OLLAMA',
                         'type': 'openAiApi', 'data': {'apiKey': 'ollama', 'url': 'http://host.orb.internal:11434/v1'}},
                         {'id': 'wonminLabDataApi', 'name': 'SUPPORT_DATA_API_X_API_KEY', 'type': 'httpHeaderAuth',
                          'data': {'name': 'X-Api-Key', 'value': private_values.get('LAB_DATA_API_KEY', private_values['INTERNAL_API_KEY'])}}])]:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        path.chmod(0o600)
    (runtime / 'team-deploy-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == '__main__':
    main()
