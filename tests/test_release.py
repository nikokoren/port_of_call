import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import deploy_cloudflare
from scripts import check_service


class DeploymentGates(unittest.TestCase):
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
