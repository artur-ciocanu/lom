"""Security checks for the optional message trace."""

import os
import stat
import tempfile
import unittest
from pathlib import Path

from main import write_trace


class TraceTests(unittest.TestCase):
    def test_trace_is_private_and_never_overwrites(self):
        with tempfile.TemporaryDirectory(dir=os.getenv("TEST_TMPDIR")) as tmp:
            path = Path(tmp) / "trace.json"
            write_trace(path, b"sensitive")
            self.assertEqual(path.read_bytes(), b"sensitive")
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                write_trace(path, b"replacement")
            self.assertEqual(path.read_bytes(), b"sensitive")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_trace_does_not_follow_a_symlink(self):
        with tempfile.TemporaryDirectory(dir=os.getenv("TEST_TMPDIR")) as tmp:
            target = Path(tmp) / "target"
            target.write_bytes(b"original")
            link = Path(tmp) / "link"
            link.symlink_to(target)
            with self.assertRaises(FileExistsError):
                write_trace(link, b"replacement")
            self.assertEqual(target.read_bytes(), b"original")
