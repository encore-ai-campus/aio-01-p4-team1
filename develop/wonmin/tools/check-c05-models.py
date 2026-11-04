#!/usr/bin/env python3
"""Review pinned Jihye C05 DTOs in memory; no API calls or other-owner file writes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

import pydantic
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
OWN = ROOT / 'develop/wonmin'
DEFAULT_REF = '4bbbf49aac652bae947fec1a787b86af7e74f24e'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default=DEFAULT_REF, help='Reviewed commit; defaults to pinned Jihye P0-2 commit')
    parser.add_argument('--output', help='New report filename under develop/wonmin/runs; never overwrites')
    args = parser.parse_args()
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', args.ref + '^{commit}'], cwd=ROOT, text=True).strip()
    for name in ('app', 'app.schemas'):
        module = types.ModuleType(name)
        module.__path__ = []
        sys.modules[name] = module
    hashes = {}
    for name in ('common', 'tickets', 'alerts'):
        path = f'develop/jihye/app/schemas/{name}.py'
        source = subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=ROOT)
        hashes[path] = hashlib.sha256(source).hexdigest()
        module = types.ModuleType(f'app.schemas.{name}')
        sys.modules[module.__name__] = module
        exec(compile(source, f'{commit}:{path}', 'exec'), module.__dict__)
    tickets, alerts = sys.modules['app.schemas.tickets'], sys.modules['app.schemas.alerts']
    # Execute the checked-in Code nodes to obtain the requests, rather than rewriting their mapping.
    node_source = r'''
import { readFileSync } from 'node:fs';
import { code } from './develop/wonmin/tests/workflow-runner.mjs';
const workflow = JSON.parse(readFileSync('develop/wonmin/workflows/oke-handoff.json'));
const node = name => workflow.nodes.find(n => n.name === name);
const samples = [];
for (const name of ['normal', 'high', 'duplicate']) {
  const input = JSON.parse(readFileSync('develop/wonmin/requests/handoff-' + name + '.json'));
  const mapped = code(node('H02 Validate and Map'), { body: input });
  if (!mapped.valid) throw Error('Invalid C04 sample');
  samples.push({ name: 'tickets-' + name, endpoint: '/tickets', stage: 'implemented_mapping', body: mapped.ticket_payload });
  if (name === 'normal') {
    for (const mode of ['practice', 'app']) {
      const state = code(node('H03 Select Store'), mapped, {}, { SERVICE_MODE: mode });
      const kept = code(node('H06 Keep Ticket'), { statusCode: 201, body: { ticket_id: 'T-2001', duplicate: false } },
        { 'H03 Select Store': state });
      samples.push({ name: 'alerts-' + mode, endpoint: '/alerts', stage: 'implemented_mapping', body: kept.alert_payload });
    }
  }
}
const state = { ticket: { ticket_id: 'T-2001', priority: 'normal', duplicate: true }, mode: 'app' };
const observe = body => code(node('H10 Build Result'), { statusCode: 200, body }, { 'H06 Keep Ticket': state }).response;
console.log(JSON.stringify({ samples, alert_probe: { raw: observe({ stored: 0, count: 1, duplicate: true }),
  serialized: observe({ stored: 0, count: 1 }) } }));
'''
    computed = json.loads(subprocess.check_output(['node', '--input-type=module', '-e', node_source], cwd=ROOT))
    samples = computed['samples']
    for request_id in ('wm-c05-ticket-failure', None):
        samples.append({'name': 'dlq-' + ('ticket-failure' if request_id else 'unexpected-error'),
                        'endpoint': '/dlq', 'stage': 'planned_P1-2_or_P1-3_not_sent',
                        'body': {'request_id': request_id, 'workflow': 'oke-handoff' if request_id else 'oke-errors',
                                 'node': 'H04 Create Ticket' if request_id else 'E02 Safe Context',
                                 'reason': 'tickets_down' if request_id else 'unexpected',
                                 'safe_payload': {'stage': 'ticket' if request_id else 'unexpected',
                                                  'priority': 'normal'},
                                 'execution_ref': 'local-review-only'}})
    models = {'/tickets': tickets.TicketCreate, '/alerts': alerts.AlertCreate, '/dlq': alerts.DlqCreate}
    checks = []
    for sample in samples:
        result = models[sample['endpoint']].model_validate(sample['body']).model_dump(exclude_unset=True)
        assert result == sample['body'], f"Sample fields discarded: {sample['name']}"
        checks.append({'name': sample['name'], 'endpoint': sample['endpoint'], 'request_model': 'accepted_no_fields_lost'})
    nullable = alerts.DlqCreate.model_fields['request_id']
    assert nullable.is_required()
    omitted = samples[-1]['body'].copy()
    omitted.pop('request_id')
    try:
        alerts.DlqCreate.model_validate(omitted)
    except ValidationError:
        missing_request_id = 'rejected_required_nullable_field'
    else:
        raise AssertionError('Recheck changed DlqCreate.request_id omission semantics')
    for body in ({'ticket_id': 'T-2001', 'duplicate': False}, {'ticket_id': 'T-2001', 'duplicate': True}):
        assert tickets.TicketCreated.model_validate(body).model_dump() == body
    assert alerts.StoredResponse.model_validate({'stored': 1, 'count': 1}).model_dump() == {'stored': 1, 'count': 1}
    duplicate_input = {'stored': 0, 'count': 1, 'duplicate': True}
    duplicate_output = alerts.StoredResponse.model_validate(duplicate_input).model_dump()
    assert duplicate_output == {'stored': 0, 'count': 1}
    assert computed['alert_probe']['raw']['alerted'] is True
    assert computed['alert_probe']['serialized']['alerted'] is False
    report = {'scope': 'pinned DTO model validation + local workflow Code; no FastAPI/n8n/DB execution',
              'jihye_commit': commit, 'pydantic_version': pydantic.__version__, 'source_sha256': hashes,
              'workflow_sha256': hashlib.sha256((OWN / 'workflows/oke-handoff.json').read_bytes()).hexdigest(),
              'samples': samples, 'request_checks': checks, 'requests_accepted': len(checks),
              'dlq_request_id_omitted': missing_request_id,
              'duplicate_alert_ack': {'backend_input': duplicate_input, 'model_output': duplicate_output,
                                      'workflow_before_serialization': computed['alert_probe']['raw'],
                                      'workflow_after_serialization': computed['alert_probe']['serialized'],
                                      'status': 'incompatible_duplicate_flag_is_discarded'},
              'service_auth_storage': 'not_run'}
    output = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        if Path(args.output).name != args.output or not args.output.endswith('.json'):
            parser.error('--output must be a .json basename under own runs/')
        with (OWN / 'runs' / args.output).open('x') as target:
            target.write(output)
        print(f'Report: develop/wonmin/runs/{args.output}')
    else:
        print(output, end='')
    print(f'Requests accepted: {len(checks)}/{len(samples)}; duplicate alert ACK: incompatible', file=sys.stderr)


if __name__ == '__main__':
    main()
