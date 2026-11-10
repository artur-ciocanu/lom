# Lom

*Lom* is Irish for [“bare” or “unadorned”](https://www.teanglann.ie/en/fgb/lom).
Lom is a coding-agent experiment built around three pillars:

- **A trivial system prompt.** The prompt states the goal, not the workflow.
- **All task-specific intelligence in skills.** Skills provide the working
  methods. The agent loads them when they are relevant.
- **All action tools through MCP. Only MCP.** File access, edits, command
  execution, and other interactions with the coding environment come from MCP
  servers. Lom registers no native action tools.

The system prompt is:

```text
Complete the user's coding task. Report what changed and what you verified.
```

PydanticAI runs the agent loop and provides `load_capability()`, a syscall-like
primitive for loading a skill's instructions. It is the only built-in tool
exposed by this setup. Everything that acts on the coding environment comes from
an MCP server.

## How it works

When you give Lom a task, PydanticAI presents the available skill descriptions
and MCP tools to the model. The model can load a relevant skill, follow its
instructions, and use the MCP tools to act. For the included demo, the
`investigate-and-fix` skill asks the agent to reproduce a failing test, make a
minimal fix, and verify the result.

The pieces are deliberately separate:

- [`agent.yaml`](agent.yaml) defines the model, system prompt, and skills
  configuration.
- [`skills/`](skills/) contains the reusable instructions.
- [`mcp.json`](mcp.json) configures the action tools.

MCP gives skills a standard tool boundary instead of tying the workflow to a
particular machine. A compatible MCP server could run locally or remotely; the
included configuration runs a local server over STDIO. MCP does not itself
sandbox that server or guarantee that different implementations behave alike.

## Try it

You need Python 3.11+, [uv](https://docs.astral.sh/uv/), and an API key for the
configured model. The default is `openai:gpt-4.1-mini`, which requires
`OPENAI_API_KEY`.

Use a disposable workspace. The fixture starts with a failing test, so copy it
rather than letting the agent change the original:

```sh
uv sync
mkdir -p /path/to/disposable-workspace
cp fixture/*.py /path/to/disposable-workspace/
printf '%s\n' 'Investigate the failing tests, fix the cause, and verify the change.' | \
  uv run python main.py --workspace /path/to/disposable-workspace
```

Lom reads the task from stdin until EOF. To enter it interactively, type the
task and press Ctrl-D (Ctrl-Z on Windows). You can also pass it as a positional
argument; that takes precedence over stdin. Empty tasks are rejected.

## Configuration

- Edit `agent.yaml` or pass `--agent PATH` to select an agent configuration.
  Pass `--model PROVIDER:MODEL` to override its model; the selected provider
  requires its own credentials.
- Edit `mcp.json` or pass `--mcp PATH` to select the MCP servers. The bundled
  server receives `--workspace` through `CODING_WORKSPACE`. Skills are resolved
  separately, relative to the Lom directory.
- Pass `--trace PATH` to save the full message history as JSON. Traces can
  contain prompts, tool arguments, and file contents; they are not redacted or
  encrypted. Lom will not overwrite an existing file or symlink and creates
  traces with owner-only permissions on Unix. Without `--trace`, it prints the
  answer and tool-call names.

## Safety

The bundled MCP server can edit files and execute commands. On macOS, its
workspace checks are **not an OS sandbox**. Use a properly configured container
or VM for untrusted code, and do not put credentials in the agent's workspace.
A STDIO server runs with the host user's permissions and may be able to access
files outside the workspace. Its default safe mode may also block commands a
task needs.

Only load trusted MCP configurations and skills: server configurations launch
processes and can interpolate environment variables, while skills and server
instructions can influence the model. Neither the system prompt nor the Git
hooks enforce runtime authorization.

## Development

Install [just](https://just.systems/) and run `just check` for lint, formatting,
type checks, and tests. `just --list` shows the individual commands; `just audit`
checks locked dependencies for known vulnerabilities. Run `just install-hooks`
to install the pre-commit checks.

The integration test uses a scripted model with the real skill loader and MCP
server. It verifies the wiring, not whether a real model can solve the task.
