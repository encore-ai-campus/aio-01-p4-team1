#!/usr/bin/env python3
"""Prepare ignored runtime secrets and a pinned, unedited backend deployment snapshot."""
from pathlib import Path
import io
import json
import os
import secrets
import subprocess
import tarfile

OWN = Path(__file__).resolve().parents[1]
ROOT = OWN.parents[1]
REF = 'c6e42df05737d4b36b0904ca5ae07cae8dd8b2a3'


def main():
    runtime = OWN / '.runtime'
    runtime.mkdir(mode=0o700, exist_ok=True)
    target = runtime / 'peer-jihye'
    commit = subprocess.check_output(['git', 'rev-parse', REF], cwd=ROOT, text=True).strip()
    if not (target / 'pyproject.toml').exists():
        archive = subprocess.check_output(['git', 'archive', commit, 'develop/jihye'], cwd=ROOT)
        target.mkdir(exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(archive)) as source:
            for member in source.getmembers():
                if not Path(member.name).is_relative_to('develop/jihye'):
                    continue
                relative = Path(member.name).relative_to('develop/jihye')
                if not relative.parts:
                    continue
                member.name = str(relative)
                source.extract(member, target, filter='data')
    envfile = runtime / 'lab.env'
    if not envfile.exists():
        values = {'LAB_DB_PASSWORD': secrets.token_hex(24), 'INTERNAL_API_KEY': secrets.token_hex(24),
                  'N8N_ENCRYPTION_KEY': secrets.token_hex(32), 'N8N_WEBHOOK_KEY': secrets.token_hex(24),
                  'LAB_ADMIN_PASSWORD': 'aA1!' + secrets.token_hex(20)}
        with envfile.open('x') as out:
            out.write(''.join(f'{key}={value}\n' for key, value in values.items()))
        envfile.chmod(0o600)
    values = dict(line.split('=', 1) for line in envfile.read_text().splitlines() if '=' in line)
    imports = runtime / 'n8n-import'
    imports.mkdir(mode=0o700, exist_ok=True)
    credentials = []
    for cid, name, header, value in [
        ('wonminLabStoreApp', 'WONMIN_APP_STORE_AUTH', 'X-Api-Key', values['INTERNAL_API_KEY']),
        ('wonminLabStorePractice', 'WONMIN_PRACTICE_STORE_AUTH', 'X-Api-Key', values['INTERNAL_API_KEY']),
        ('wonminLabTeam', 'WONMIN_X_TEAM_KEY', 'X-Team-Key', values['N8N_WEBHOOK_KEY']),
    ]:
        credentials.append({'id': cid, 'name': name, 'type': 'httpHeaderAuth', 'data': {'name': header, 'value': value}})
    f = imports / 'credentials.json'
    f.write_text(json.dumps(credentials))
    f.chmod(0o600)
    (runtime / 'provenance.json').write_text(json.dumps({'jihye_commit': commit, 'purpose': 'unedited deployment snapshot'}, indent=2) + '\n')
    print(json.dumps({'prepared': True, 'backend_commit': commit, 'secret_values_printed': False}))


if __name__ == '__main__':
    main()
