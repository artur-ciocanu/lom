"""Check the credential-path guard without handling actual credentials."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_sensitive_paths import is_sensitive_path


class SensitivePathTests(unittest.TestCase):
    def test_blocks_common_credential_paths(self):
        for path in (
            ".env",
            "nested/.env.production",
            ".envrc",
            ".netrc",
            ".pypirc",
            "keys/id_rsa",
            "keys/id_ed25519",
            "keys/private.PEM",
            "keys/private.key",
            "keys/private.p12",
            "keys/private.pfx",
        ):
            with self.subTest(path=path):
                self.assertTrue(is_sensitive_path(path))

    def test_allows_example_and_ordinary_files(self):
        for path in (".env.example", "nested/.env.example", "README.md", "env.py"):
            with self.subTest(path=path):
                self.assertFalse(is_sensitive_path(path))

    def test_force_added_env_is_rejected(self):
        script = (
            Path(__file__).resolve().parents[1] / "scripts/check_sensitive_paths.py"
        )
        with tempfile.TemporaryDirectory(dir=os.getenv("TEST_TMPDIR")) as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / ".gitignore").write_text(".env\n")
            (root / ".env").write_text("PLACEHOLDER=not-a-secret\n")
            subprocess.run(["git", "add", "-f", ".env"], cwd=root, check=True)
            for arguments in ([], ["--tracked"]):
                result = subprocess.run(
                    [sys.executable, str(script), *arguments],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn(".env", result.stderr)
