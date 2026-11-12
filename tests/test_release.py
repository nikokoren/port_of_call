import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,MagicMock
from scripts import deploy_cloudflare
from scripts import check_service


class DeploymentGates(unittest.TestCase):
    def test_full_probe_honors_rate_limit_without_hiding_other_http_errors(self):
        def reply(status,headers=None):
            response=MagicMock();response.status=status;response.headers=headers or {}
            response.read.return_value=b'{"status":"test"}'
            response.__enter__.return_value=response
            return response
        for delay,expected in [('60',60),('bad',60),('999',60)]:
            with patch.object(check_service,'urlopen',side_effect=[reply(429,{'Retry-After':delay}),reply(200)]) as request, \
                 patch.object(check_service.time,'sleep') as sleep:
                self.assertEqual(check_service.get('https://example.test')[0],200)
                sleep.assert_called_once_with(expected);self.assertEqual(request.call_count,2)
        with patch.object(check_service,'urlopen',return_value=reply(503)) as request, \
             patch.object(check_service.time,'sleep') as sleep:
            self.assertEqual(check_service.get('https://example.test')[0],503)
            sleep.assert_not_called();self.assertEqual(request.call_count,1)

    def test_monitor_retains_aggregate_failure_evidence_when_origin_is_unreachable(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'report.json'
            with patch('sys.argv', ['check_service', 'https://example.invalid', '--output', str(path)]), \
                 patch.object(check_service, 'check', side_effect=ConnectionError('test only')):
                with self.assertRaises(SystemExit) as exit:
                    check_service.main()
            self.assertEqual(exit.exception.code, 1)
            data = json.loads(path.read_text())
            self.assertFalse(data['passed']);self.assertEqual(data['snapshots'], [])
            self.assertEqual(data['errors'], ['ConnectionError'])

    def test_public_ais_requires_reviewed_permission_before_any_deploy(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);(root/'deploy').mkdir()
            (root/'deploy/aisstream-rights.json').write_text(json.dumps(dict(confirmed=False)))
            with patch.object(deploy_cloudflare, 'ROOT', root), patch.dict(os.environ, {
                    'CLOUDFLARE_ACCOUNT_ID': 'a'*32, 'CLOUDFLARE_API_TOKEN': 'test-only',
                    'AISSTREAM_API_KEY': 'test-only'}, clear=True):
                with self.assertRaisesRegex(ValueError, 'public use remains blocked'):
                    deploy_cloudflare.deployment_config('aisstream')

    def test_finnish_deployment_requires_host_credentials_but_no_ais_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'CLOUDFLARE_ACCOUNT_ID'):
                deploy_cloudflare.deployment_config('digitraffic')
        with patch.dict(os.environ, {'CLOUDFLARE_ACCOUNT_ID': 'a'*32, 'CLOUDFLARE_API_TOKEN': 'test-only'}, clear=True):
            deploy_cloudflare.deployment_config('digitraffic')

    def test_reviewed_ais_deployment_still_requires_secure_source_key(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);(root/'deploy').mkdir()
            (root/'deploy/aisstream-rights.json').write_text(json.dumps(dict(confirmed=True, reference='https://example.invalid/test-only-terms')))
            with patch.object(deploy_cloudflare, 'ROOT', root), patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ValueError, 'AISSTREAM_API'):
                    deploy_cloudflare.deployment_config('aisstream')

    def test_only_the_world_deploy_moves_the_primary_release(self):
        self.assertEqual(deploy_cloudflare.release_files('aisstream'), ['world-release.json', 'release.json'])
        self.assertEqual(deploy_cloudflare.release_files('digitraffic'), ['finland-release.json'])

    def test_validation_waits_only_for_post_restart_freshness(self):
        catching_up = dict(passed=False, errors=['charleston: stale', 'rotterdam: warming'])
        self.assertTrue(deploy_cloudflare.only_catching_up(catching_up))
        for errors in (['Invalid route accepted'], ['rotterdam: stale', 'Selected harbor not pinned'],
                       ['rotterdam: unavailable'], []):
            self.assertFalse(deploy_cloudflare.only_catching_up(dict(passed=not errors, errors=errors)))


class FinnishPortsInWorldRotation(unittest.TestCase):
    def test_world_serves_its_own_harbors_then_the_finnish_ones(self):
        from port_of_call.catalog import served_harbors, verified_harbors
        world, finnish = served_harbors('aisstream'), verified_harbors('digitraffic')
        self.assertEqual(list(world)[-len(finnish):], list(finnish))
        self.assertTrue(set(verified_harbors('aisstream')) < set(world))
        self.assertEqual(served_harbors('digitraffic'), finnish)

    def test_world_deploy_config_binds_the_finnish_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'cloudflare').mkdir()
            base = json.loads((Path(__file__).resolve().parents[1]/'cloudflare/wrangler.jsonc').read_text())
            (root/'cloudflare/wrangler.jsonc').write_text(json.dumps(base))
            with patch.object(deploy_cloudflare, 'ROOT', root):
                config = json.loads(deploy_cloudflare.world_config().read_text())
        self.assertEqual(config['services'], [{'binding': 'FINLAND', 'service': 'port-of-call'}])
        self.assertEqual(config['durable_objects'], base['durable_objects'])
        self.assertNotIn('services', base)


class MonitorRotationCheck(unittest.TestCase):
    """The hourly monitor must accept a rotation that lands on a forwarded harbor."""

    def fake_service(self, rotation_lands_on):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        def port(i): return dict(id=i, provider='aisstream')
        def snapshot(i): return dict(schema_version=1, demo=False, port=port(i), status='ok', shown=1, total=1,
                                     vessels=[dict(mmsi='211000001', position=[9.9, 53.5], reported_at=now)])
        def get(url):
            path = url.split('example.test', 1)[1]
            if path == '/health': return 200, dict(status='ready', provider='aisstream'), 10, {}
            if path == '/api/v1/harbors': return 200, dict(harbors=[port('hamburg')], forwarded=['helsinki']), 10, {}
            if path.startswith('/api/v1/harbors/hamburg/vessels?scale=bad'): return 400, {}, 0, {}
            if path.startswith('/api/v1/harbors/hamburg/vessels'): return 200, snapshot('hamburg'), 100, {}
            if path.startswith('/api/v1/vessels?harbors=&'): return 200, snapshot(rotation_lands_on), 100, {}
            if path.startswith('/api/v1/vessels?harbors=hamburg&spotlight=maybe'): return 400, {}, 0, {}
            for harbor in ('hamburg', 'helsinki'):
                if path.startswith('/api/v1/vessels?harbors='+harbor+'&'): return 200, snapshot(harbor), 100, {}
            return 404, {}, 0, {}
        return get

    def test_empty_selection_may_land_on_a_forwarded_harbor(self):
        for landed, ok in (('hamburg', True), ('helsinki', True), ('rotterdam', False)):
            with patch.object(check_service, 'get', self.fake_service(landed)):
                report = check_service.check('https://example.test')
            self.assertEqual(report['passed'], ok, (landed, report['errors']))
