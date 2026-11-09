"""Exercise the real skill loader and MCP server with a scripted model.

This verifies wiring and tool behavior, not an LLM's ability to solve a task.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from main import build_agent

ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_skill_and_real_mcp_coding_workflow(self):
        steps = [
            ("load_capability", {"id": "investigate-and-fix"}),
            (
                "coding_exec_command",
                {"cmd": "python3 -B -m unittest discover", "yield_time_ms": 10000},
            ),
            ("coding_read_file", {"path": "calculator.py"}),
            (
                "coding_apply_patch",
                {
                    "patch": (
                        "*** Begin Patch\n"
                        "*** Update File: calculator.py\n"
                        "@@\n"
                        "-    return right - left\n"
                        "+    return left - right\n"
                        "*** End Patch"
                    )
                },
            ),
            (
                "coding_exec_command",
                {"cmd": "python3 -B -m unittest discover", "yield_time_ms": 10000},
            ),
        ]
        calls = []
        instructions_after_load = []

        def scripted_model(messages, info):
            if not calls:
                names = {tool.name for tool in info.function_tools}
                self.assertIn("load_capability", names)
                self.assertIn("coding_apply_patch", names)
                self.assertTrue(
                    all(
                        name == "load_capability" or name.startswith("coding_")
                        for name in names
                    )
                )
                self.assertIn("investigate-and-fix", info.instructions)
            elif len(calls) == 1:
                instructions_after_load.append(str(messages[-1].parts))
            if len(calls) == len(steps):
                return ModelResponse(parts=[TextPart("Scripted integration complete.")])
            name, args = steps[len(calls)]
            calls.append(name)
            return ModelResponse(parts=[ToolCallPart(name, args)])

        with tempfile.TemporaryDirectory(
            prefix="mcp-skills-test-", dir=os.getenv("TEST_TMPDIR")
        ) as tmp:
            workspace = Path(tmp)
            for source in (ROOT / "fixture").glob("*.py"):
                shutil.copy(source, workspace / source.name)
            with patch.dict(
                os.environ,
                {"CODING_WORKSPACE": str(workspace), "PYDANTIC_AI_NO_BANNER": "1"},
            ):
                agent = build_agent(
                    ROOT / "agent.yaml",
                    ROOT / "mcp.json",
                    model=FunctionModel(scripted_model),
                )
                result = await agent.run("Run the scripted coding workflow.")

            returns = [
                part
                for message in result.all_messages()
                for part in message.parts
                if part.part_kind == "tool-return"
            ]
            self.assertEqual(calls, [name for name, _ in steps])
            self.assertEqual(len(returns), len(steps))
            self.assertIn("Verification:", instructions_after_load[0])
            self.assertIn("FAILED", str(returns[1].content))
            self.assertIn("return right - left", str(returns[2].content))
            self.assertIn("left - right", (workspace / "calculator.py").read_text())
            self.assertIn("OK", str(returns[4].content))
            self.assertEqual(result.output, "Scripted integration complete.")
            # Message histories, including tool calls, must be serializable for traces.
            self.assertIsInstance(json.loads(result.all_messages_json()), list)


if __name__ == "__main__":
    unittest.main()
