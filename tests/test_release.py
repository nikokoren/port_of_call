import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import deploy_cloudflare


class DeploymentGates(unittest.TestCase):
    def test_public_ais_requires_reviewed_permission_before_any_deploy(self):
        with patch.dict(os.environ, {'CLOUDFLARE_ACCOUNT_ID': 'a'*32, 'CLOUDFLARE_API_TOKEN': 'test-only',
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
