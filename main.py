"""Run an agent assembled from a PydanticAI spec, skills, and MCP JSON."""

import argparse
import asyncio
import os
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.mcp import load_mcp_toolsets
from pydantic_ai.models import Model
from pydantic_ai.usage import UsageLimits
from pydantic_ai_harness import Skills

ROOT = Path(__file__).resolve().parent


def build_agent(
    agent_path: Path, mcp_path: Path, *, model: Model | str | None = None
) -> Agent:
    """Assemble the agent using PydanticAI's existing loaders."""
    return Agent.from_file(
        agent_path,
        custom_capability_types=[Skills],
        toolsets=load_mcp_toolsets(mcp_path),
        model=model,
    )


def write_trace(path: Path, content: bytes) -> None:
    """Create a private trace without overwriting an existing file or symlink."""
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "wb") as trace:
        trace.write(content)


async def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Task for the agent")
    parser.add_argument(
        "--workspace", type=Path, required=True, help="Existing coding workspace"
    )
    parser.add_argument("--agent", type=Path, default=ROOT / "agent.yaml")
    parser.add_argument("--mcp", type=Path, default=ROOT / "mcp.json")
    parser.add_argument("--model", help="Override the model in the agent spec")
    parser.add_argument(
        "--trace",
        type=Path,
        help="Save full message history as JSON (may contain sensitive data)",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve(strict=True)
    agent_path = args.agent.resolve()
    mcp_path = args.mcp.resolve()
    trace_path = args.trace.absolute() if args.trace else None
    if not workspace.is_dir():
        parser.error("--workspace must be a directory")

    # Skills resolve from this experiment's directory; the MCP server receives
    # the separate coding workspace via its configuration.
    os.chdir(ROOT)
    os.environ["CODING_WORKSPACE"] = str(workspace)
    agent = build_agent(agent_path, mcp_path, model=args.model)
    result = await agent.run(args.task, usage_limits=UsageLimits(request_limit=30))

    print(result.output)
    print("\nTool calls:")
    for message in result.all_messages():
        for part in message.parts:
            if part.part_kind == "tool-call":
                print(f"  {part.tool_name}")

    if trace_path:
        write_trace(trace_path, result.all_messages_json())
        print(f"\nFull trace saved to {trace_path}")


if __name__ == "__main__":
    asyncio.run(run())
