"""Static n8n graph gates; not an n8n execution test."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class WorkflowStructureTests(unittest.TestCase):
    def test_graph_references_and_inactive_deployment_gate(self):
        for filename in ('oke-index.json','oke-search.json'):
            with self.subTest(filename=filename):
                workflow=json.loads((ROOT/'workflows'/filename).read_text())
                self.assertIs(workflow['active'],False)
                nodes=workflow['nodes'];names={n['name'] for n in nodes}
                self.assertEqual(len(names),len(nodes))
                self.assertEqual(len({n['id'] for n in nodes}),len(nodes))
                graph={n:[] for n in names}
                for source,types in workflow['connections'].items():
                    self.assertIn(source,names)
                    for branches in types.values():
                        for targets in branches:
                            for target in targets:
                                self.assertIn(target['node'],names)
                                self.assertEqual(target['type'],'main')
                                graph[source].append(target['node'])
                starts=[n['name'] for n in nodes if n['type'].endswith(('.webhook','.manualTrigger'))]
                reached=set();pending=list(starts)
                while pending:
                    name=pending.pop()
                    if name not in reached:
                        reached.add(name);pending.extend(graph[name])
                self.assertEqual(reached,names)
                for node in nodes:
                    if node['type'].endswith('.httpRequest'):
                        self.assertEqual(node['parameters']['genericAuthType'],'httpHeaderAuth')
                        self.assertTrue(node['parameters']['url'].startswith('={{ $env.'))
                        self.assertNotIn('credentials',node)
