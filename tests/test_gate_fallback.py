"""The pure-JS fallback must decrypt exactly what gate.py encrypts.

Runs the fallback under node against a real payload. Skips silently only
if node is absent (CI-less repo; dev machines have it)."""

import base64
import json
import shutil
import subprocess
import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gate import encrypt_payload
from gate_fallback import FALLBACK_JS

HTML = "<!doctype html><html><body>fallback proof é✓</body></html>"
PASS = "YB-TEST-CODE"

NODE_HARNESS = """
%s
const payload = Buffer.from(process.argv[2], 'base64');
const salt = new Uint8Array(payload.subarray(0, 16));
const ct = new Uint8Array(payload.subarray(16));
global.TextEncoder = require('util').TextEncoder;
const pt = YBF.decrypt(process.argv[3], salt, ct);
process.stdout.write(pt ? Buffer.from(pt).toString('utf8') : '<<FAIL>>');
"""


@unittest.skipUnless(shutil.which("node"), "node not available")
class TestFallbackDecrypt(unittest.TestCase):
    def run_node(self, payload, passcode):
        harness = NODE_HARNESS % FALLBACK_JS
        return subprocess.run(
            ["node", "-", payload, passcode], input=harness,
            capture_output=True, text=True, timeout=120)

    def test_decrypts_real_payload(self):
        payload = encrypt_payload(HTML, PASS)
        r = self.run_node(payload, PASS)
        self.assertEqual(r.stdout, HTML, r.stderr[:400])

    def test_wrong_pass_fails_closed(self):
        payload = encrypt_payload(HTML, PASS)
        r = self.run_node(payload, "YB-WRONG-CODE")
        self.assertNotEqual(r.stdout, HTML)


if __name__ == "__main__":
    unittest.main()
