"""Member gate: the members pages ship AES-encrypted in the public repo.

Key derivation is PBKDF2-HMAC-SHA256 (200k iters) in Python stdlib; the
cipher runs through the system openssl binary (raw -K/-iv mode, works on
both OpenSSL and LibreSSL). The browser side re-derives with WebCrypto
using identical parameters. No passphrase -> no shell, caller decides.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gate import decrypt_html, encrypt_payload, gate_page_html

HTML = "<!doctype html><html><body><h1>MEMBERS ONLY</h1>secret alpha</body></html>"
PASS = "YB-TEST-CODE"


class TestEncryptRoundtrip(unittest.TestCase):
    def test_roundtrip(self):
        payload = encrypt_payload(HTML, PASS)
        self.assertEqual(decrypt_html(payload, PASS), HTML)

    def test_wrong_pass_fails(self):
        payload = encrypt_payload(HTML, PASS)
        out = decrypt_html(payload, "YB-WRONG-CODE")
        self.assertNotEqual(out, HTML)  # garbage or None, never the content

    def test_payload_hides_plaintext(self):
        payload = encrypt_payload(HTML, PASS)
        self.assertNotIn("MEMBERS ONLY", payload)
        self.assertNotIn("secret alpha", payload)

    def test_fresh_salt_every_time(self):
        self.assertNotEqual(encrypt_payload(HTML, PASS),
                            encrypt_payload(HTML, PASS))


class TestGatePage(unittest.TestCase):
    def shell(self):
        return gate_page_html(encrypt_payload(HTML, PASS), "Young Bull Members")

    def test_shell_contains_payload_not_content(self):
        shell = self.shell()
        self.assertNotIn("secret alpha", shell)
        self.assertIn("YB_GATE", shell)          # payload marker
        self.assertIn("PBKDF2", shell)           # webcrypto derive present
        self.assertIn("AES-CBC", shell)
        self.assertIn("200000", shell)           # iterations must match python
        self.assertIn("localStorage", shell)     # passcode remembered

    def test_shell_has_no_em_dash_and_is_titled(self):
        shell = self.shell()
        self.assertNotIn("—", shell)
        self.assertIn("<title>Young Bull Members</title>", shell)


if __name__ == "__main__":
    unittest.main()
