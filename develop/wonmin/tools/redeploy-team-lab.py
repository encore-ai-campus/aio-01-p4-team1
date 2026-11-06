#!/usr/bin/env python3
"""Back up and redeploy only the existing private Ubuntu lab; never delete volumes."""
import datetime
import importlib.util
import json
from pathlib import Path
import subprocess
import time
import urllib.error

OWN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab', OWN / 'tools/linux-lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def ready():
    for _ in range(60):
        try:
            if lab.request(15678, '/healthz')['status'] == 200:
                return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    raise RuntimeError('n8n readiness timeout')


def main():
    assert 'ubuntu' in Path('/etc/os-release').read_text().lower()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    private = OWN / '.runtime' / 'backups' / stamp
    private.mkdir(parents=True, mode=0o700)
    ids = json.loads((OWN / '.runtime/workflow-ids.json').read_text())
    report = {'source_manifest': json.loads((OWN / '.runtime/team-deploy-manifest.json').read_text()),
              'started_utc': stamp, 'stages': []}

    def done(name):
        report['stages'].append(name)
        print(json.dumps({'stage': name}), flush=True)

    before = lab.command(['docker', 'exec', 'wonmin-p13-lab-n8n-1', 'node', '-e',
        'const{DatabaseSync}=require("node:sqlite");const d=new DatabaseSync("/home/node/.n8n/database.sqlite",{readOnly:true});console.log(JSON.stringify({users:d.prepare("SELECT count(*) AS n FROM user").get().n,assistant:d.prepare("SELECT value FROM settings WHERE key=?").get("instanceAi.settings")?.value??null}));'])
    (private / 'before-state.json').write_text(before)
    (private / 'before-state.json').chmod(0o600)
    lab.command(['docker', 'exec', 'wonmin-p13-lab-n8n-1', 'node', '-e',
        'const{DatabaseSync,backup}=require("node:sqlite");const d=new DatabaseSync("/home/node/.n8n/database.sqlite",{readOnly:true});backup(d,"/tmp/wonmin-predeploy.sqlite").then(()=>{d.close();console.log("backup_complete")})'])
    lab.command(['docker', 'cp', 'wonmin-p13-lab-n8n-1:/tmp/wonmin-predeploy.sqlite', str(private / 'n8n.sqlite')])
    (private / 'n8n.sqlite').chmod(0o600)
    with (private / 'postgres.sql').open('xb') as target:
        (private / 'postgres.sql').chmod(0o600)
        result = subprocess.run(lab.COMPOSE + ['exec', '-T', 'postgres', 'sh', '-c',
                 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h 127.0.0.1 -U "$POSTGRES_USER" "$POSTGRES_DB"'],
                 stdout=target, stderr=subprocess.PIPE, timeout=90)
        assert result.returncode == 0, 'private PostgreSQL backup failed'
    done('private_n8n_and_postgres_backups_complete')
    lab.compose('config', '--quiet')
    for service in ('backend', 'rag-search', 'n8n'):
        result = subprocess.run(lab.COMPOSE + ['build', service], text=True, capture_output=True, timeout=600)
        (private / (service + '-build.log')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(service + ' image build failed; inspect private build log')
        if service == 'rag-search':
            expected = ['python', 'tools/search_http.py', '--host', '0.0.0.0', '--port', '8765']
            actual = json.loads(lab.command(['docker', 'image', 'inspect', 'wonmin-rag-lab:95ef45f', '--format', '{{json .Config.Cmd}}']))
            if actual != expected:
                lab.compose('build', '--no-cache', 'rag-search', timeout=300)
                actual = json.loads(lab.command(['docker', 'image', 'inspect', 'wonmin-rag-lab:95ef45f', '--format', '{{json .Config.Cmd}}']))
            assert actual == expected, 'RAG image command must be verified before starting the service'
        done(service + '_built')
    lab.compose('up', '-d', 'postgres', 'backend', 'rag-search', 'mock-store', 'n8n', timeout=180)
    ready()
    for _ in range(30):
        try:
            network = lab.compose('exec', '-T', 'n8n', 'node', '-e',
                'fetch("http://rag-search:8765/webhook/oke-search",{method:"POST",body:"{}"}).then(r=>{if(r.status!==401)process.exitCode=1}).catch(()=>{process.exitCode=1})')
            break
        except RuntimeError:
            time.sleep(1)
    else:
        raise RuntimeError('n8n cannot reach the authenticated RAG service')
    done('five_services_started_existing_volumes_preserved')
    report['migration'] = lab.compose('exec', '-T', 'backend', 'uv', 'run', 'alembic', '-c', 'migrations/alembic.ini', 'upgrade', 'head').strip()
    done('peer_migrations_upgraded_to_head')
    lab.compose('exec', '-T', 'n8n', 'n8n', 'import:credentials', '--input=/fixtures/private/team-credentials.json')
    lab.compose('exec', '-T', 'n8n', 'n8n', 'import:workflow', '--input=/fixtures/private/team-workflows.json')
    for key in ('errors', 'handoff', 'search', 'support'):
        lab.compose('exec', '-T', 'n8n', 'n8n', 'publish:workflow', '--id=' + ids[key])
    lab.compose('restart', 'n8n')
    ready()
    time.sleep(2)
    done('five_team_workflows_imported_four_published_index_manual_draft')
    report['workflows'] = lab.metadata('workflows', ids)
    after = lab.command(['docker', 'exec', 'wonmin-p13-lab-n8n-1', 'node', '-e',
        'const{DatabaseSync}=require("node:sqlite");const d=new DatabaseSync("/home/node/.n8n/database.sqlite",{readOnly:true});console.log(JSON.stringify({users:d.prepare("SELECT count(*) AS n FROM user").get().n,assistant:d.prepare("SELECT value FROM settings WHERE key=?").get("instanceAi.settings")?.value??null}));'])
    assert json.loads(before) == json.loads(after), 'existing users or Assistant settings changed'
    report['users_and_assistant_preserved'] = True
    done('users_and_existing_assistant_settings_preserved')
    report['index_engine'] = json.loads(lab.compose('exec', '-T', 'n8n', 'python3', '/opt/oke-rag/tools/rag_verify.py',
                                            'index', '--source', 'mock', '--scenario', 'initial-and-repeat', '--json'))
    assert report['index_engine']['ok'] and report['index_engine']['mode'] == 'mock'
    done('index_python_engine_mock_verified_in_actual_n8n_container')
    result = subprocess.run(lab.COMPOSE + ['exec','-T','-e','OKE_RUN_DB_TESTS=1','backend','uv','run','pytest','-q','tests/integration'],
                            text=True, capture_output=True, timeout=120)
    report['postgres_tests'] = {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    assert result.returncode == 0, 'peer actual PostgreSQL integration tests failed'
    done('latest_peer_postgres_tests_passed')
    values = dict(line.split('=', 1) for line in lab.ENVFILE.read_text().splitlines() if '=' in line)
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    assert not any(v in text for v in values.values() if len(v) >= 16)
    with (OWN / 'runs' / ('team-redeploy-' + stamp + '.json')).open('x') as output:
        output.write(text)
    print(json.dumps({'report': 'team-redeploy-' + stamp + '.json'}), flush=True)


if __name__ == '__main__':
    main()
