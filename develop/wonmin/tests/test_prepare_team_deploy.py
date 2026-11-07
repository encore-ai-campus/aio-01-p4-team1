"""Real temporary Git repositories catch deployment/source provenance drift."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/prepare-team-deploy.py'


class PrepareTeamDeployTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wonmin-deploy-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.own = self.root / 'develop/wonmin'
        self.git('init', '-q', '-b', 'main')
        self.support = self.root / 'develop/dahyeok/workflows/oke-support-13.json'
        for path, name, nodes in [
            (self.support, 'oke-support', [{'name': 'behavior', 'type': 'n8n-nodes-base.code', 'parameters': {'jsCode': 'return "approved-v1";'}}]),
            (self.root/'develop/yubeen/workflows/oke-search.json', 'oke-search', []),
            (self.root/'develop/yubeen/workflows/oke-index.json', 'oke-index', [{'name': 'engine', 'type': 'n8n-nodes-base.executeCommand', 'parameters': {'command': 'python3 engine.py --source mock'}}]),
            (self.root/'develop/jihye/app.json', 'backend-snapshot', []),
            (self.own/'workflows/oke-handoff.json', 'oke-handoff', []),
            (self.own/'workflows/oke-errors.json', 'oke-errors', []),
        ]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({'name': name, 'active': False, 'nodes': nodes, 'settings': {}}))
        self.git('add', '.')
        self.git('commit', '-qm', 'approved initial source')
        self.first = self.git('rev-parse', 'HEAD').strip()
        self.runtime = self.own / '.runtime'
        (self.runtime/'n8n-import').mkdir(parents=True)
        (self.runtime/'lab.env').write_text('INTERNAL_API_KEY=synthetic-test-value-only\n')
        (self.runtime/'workflow-ids.json').write_text(json.dumps(dict(errors='err', handoff='han', failure='fail', llm='llm')))
        spec = importlib.util.spec_from_file_location('prepare_under_test', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.module.ROOT, self.module.OWN = self.root, self.own
        self.module.SOURCES = dict(jihye=self.first, yubeen=self.first, dahyeok=self.first)

    def git(self, *args):
        return subprocess.check_output(['git', '-c', 'user.name=Deployment Fixture', '-c', 'user.email=fixture@example.invalid', *args],
                                       cwd=self.root, text=True, stderr=subprocess.PIPE)

    def change_support(self):
        data = json.loads(self.support.read_text())
        data['nodes'][0]['parameters']['jsCode'] = 'return "unreviewed-v2";'
        self.support.write_text(json.dumps(data))

    def prepare(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.module.main()
        manifest = json.loads((self.runtime/'team-deploy-manifest.json').read_text())
        workflows = json.loads((self.runtime/'n8n-import/team-workflows.json').read_text())
        return manifest, next(w for w in workflows if w['name'] == 'oke-support')

    def test_pinned_source_is_not_replaced_by_a_dirty_working_file(self):
        approved = self.support.read_bytes()
        self.change_support()
        manifest, workflow = self.prepare()
        self.assertEqual(workflow['nodes'][0]['parameters']['jsCode'], 'return "approved-v1";')
        row = next(w for w in manifest['workflows'] if w['name'] == 'oke-support')
        self.assertEqual(row['source_sha256'], hashlib.sha256(approved).hexdigest())

    def test_updating_the_pin_materializes_the_new_committed_behavior(self):
        self.change_support()
        self.git('add', str(self.support.relative_to(self.root)))
        self.git('commit', '-qm', 'approved next behavior')
        second = self.git('rev-parse', 'HEAD').strip()
        self.module.SOURCES['dahyeok'] = second
        manifest, workflow = self.prepare()
        self.assertEqual(workflow['nodes'][0]['parameters']['jsCode'], 'return "unreviewed-v2";')
        row = next(w for w in manifest['workflows'] if w['name'] == 'oke-support')
        self.assertEqual(row.get('source_commit'), second)

    def test_unmerged_dahyeok_pin_is_rejected_before_creating_import_files(self):
        self.git('checkout', '-qb', 'unmerged-candidate')
        self.change_support()
        self.git('add', str(self.support.relative_to(self.root)))
        self.git('commit', '-qm', 'candidate not integrated')
        self.module.SOURCES['dahyeok'] = self.git('rev-parse', 'HEAD').strip()
        self.git('checkout', '-q', 'main')
        with self.assertRaises(subprocess.CalledProcessError):
            self.prepare()
        self.assertFalse((self.runtime/'n8n-import/team-workflows.json').exists())


if __name__ == '__main__':
    unittest.main()
