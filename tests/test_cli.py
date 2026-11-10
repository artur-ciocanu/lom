"""Check prompt input without making model or MCP requests."""

import io
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from main import run


class PromptInputTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdin_prompt_preserves_multiline_text(self):
        with tempfile.TemporaryDirectory(dir=os.getenv("TEST_TMPDIR")) as workspace:
            agent = MagicMock()
            agent.run = AsyncMock(
                return_value=MagicMock(output="done", all_messages=list)
            )
            with (
                patch(
                    "sys.argv",
                    ["main.py", "--workspace", workspace, "--model", "test:model"],
                ),
                patch("sys.stdin", io.StringIO("first line\nsecond line\n")),
                patch("sys.stdout", new_callable=io.StringIO),
                patch("os.chdir"),
                patch.dict(os.environ),
                patch("main.build_agent", return_value=agent),
            ):
                await run()
            self.assertEqual(agent.run.await_args.args[0], "first line\nsecond line\n")

    async def test_positional_prompt_takes_precedence(self):
        with tempfile.TemporaryDirectory(dir=os.getenv("TEST_TMPDIR")) as workspace:
            agent = MagicMock()
            agent.run = AsyncMock(
                return_value=MagicMock(output="done", all_messages=list)
            )
            with (
                patch(
                    "sys.argv",
                    [
                        "main.py",
                        "--workspace",
                        workspace,
                        "--model",
                        "test:model",
                        "explicit",
                    ],
                ),
                patch("sys.stdin", io.StringIO("ignored")),
                patch("sys.stdout", new_callable=io.StringIO),
                patch("os.chdir"),
                patch.dict(os.environ),
                patch("main.build_agent", return_value=agent),
            ):
                await run()
            self.assertEqual(agent.run.await_args.args[0], "explicit")

    async def test_empty_stdin_is_rejected_before_agent_is_built(self):
        with tempfile.TemporaryDirectory(dir=os.getenv("TEST_TMPDIR")) as workspace:
            with (
                patch(
                    "sys.argv",
                    ["main.py", "--workspace", workspace, "--model", "test:model"],
                ),
                patch("sys.stdin", io.StringIO(" \n")),
                patch("sys.stderr", new_callable=io.StringIO) as stderr,
                patch("main.build_agent") as build_agent,
                self.assertRaises(SystemExit) as error,
            ):
                await run()
            self.assertEqual(error.exception.code, 2)
            self.assertIn("non-empty task", stderr.getvalue())
            build_agent.assert_not_called()

    async def test_model_is_required(self):
        with tempfile.TemporaryDirectory(dir=os.getenv("TEST_TMPDIR")) as workspace:
            with (
                patch("sys.argv", ["main.py", "--workspace", workspace, "task"]),
                patch("sys.stderr", new_callable=io.StringIO) as stderr,
                patch("main.build_agent") as build_agent,
                self.assertRaises(SystemExit) as error,
            ):
                await run()
            self.assertEqual(error.exception.code, 2)
            self.assertIn("--model", stderr.getvalue())
            build_agent.assert_not_called()
