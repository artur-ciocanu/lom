# MCP and skills experiment

A small PydanticAI agent assembled from `agent.yaml`, an Agent Skills directory,
and the MCP servers in `mcp.json`. The launcher exposes no native action tools;
PydanticAI supplies `load_capability` for on-demand skills, and MCP supplies
task-facing actions. This is not yet an Agent Plugins client.

## Run

Requirements: Python 3.11+, [uv](https://docs.astral.sh/uv/), and an API key
for the model in `agent.yaml` (`OPENAI_API_KEY` for the default). The first run
downloads the locked Python dependencies, including the MCP server, from PyPI.

```sh
uv sync
mkdir -p /path/to/disposable-workspace
cp fixture/*.py /path/to/disposable-workspace/
uv run python main.py --workspace /path/to/disposable-workspace \
  'Investigate the failing tests, fix the cause, and verify the change.'
```

Pass `--model openai:MODEL` to override the agent spec (with the matching
provider API key). Pass `--trace PATH` to
save the full PydanticAI message history as JSON; it can contain prompts,
tool arguments, file contents, and other sensitive data. Without that flag,
the launcher prints only the answer and tool-call names. On Unix, traces are
created with owner-only permissions; an existing file or symlink is not
overwritten. Traces are not redacted or encrypted.

Google's Gemini SDK in the current lockfile defaults to API `v1`, which rejected
function calling during our test. A custom `v1beta` client reached the model but
hit its rate limit; the plain `google:` model override has not been verified.

`agent.yaml` resolves skills against this directory. `--workspace` is passed to
the MCP server separately via `CODING_WORKSPACE`. PydanticAI's MCP loader
prefixes tool names with their server name. The sample `mcp.json` is the
PydanticAI/Claude-style format, not a conformant Agent Plugins configuration.

## Development checks

Install [just](https://just.systems/) and run `just check` for Ruff lint and
format checks, Pyright, and the integration test. `just audit` checks locked
dependencies for known vulnerabilities. Individual recipes are shown by
`just --list`. The integration test drives the locked MCP server with a
scripted PydanticAI model and a temporary copy
of the fixture. It verifies wiring, not whether a real model can solve the task.
Use `just format` to apply formatting, and `just sync` to install the locked
dependencies. `uv.lock` records the resolved versions, including dev tools.

Run `just install-hooks` once after cloning to install the pre-commit hook.
It blocks common credential-file paths, uses a pinned Gitleaks version to scan
staged changes, then runs Ruff and Pyright. The Gitleaks hook builds using Go
on first install; the other hooks use the uv-managed development dependencies.
`.env`, private key files, and traces are ignored by Git. Secret scanning is
a safeguard, not a guarantee:
review changes before publishing and never commit real credentials. The GitHub
Actions workflow scans reachable Git history and locked dependencies on pushes,
pull requests, and weekly. Hooks can be bypassed and CI cannot retract secrets
already pushed; rotate any exposed credentials immediately.

## Safety and scope

Use a disposable workspace. The sample MCP server can edit files and execute
commands; on macOS, its workspace checks are **not an OS sandbox**. Use a
properly configured container or VM for untrusted code. Its default safe mode
may block commands the task needs. Never put credentials in the agent's
workspace: Git ignore rules do not prevent MCP tools or commands from reading
files. A stdio server runs with the host user's permissions and may be able to
read files outside the workspace. Only load trusted MCP configs and skills:
server configuration launches processes and can interpolate environment
variables, while skills and MCP server instructions can influence the model.
Neither the system prompt nor the hooks enforce runtime authorization.

The fixture intentionally starts with failing tests. Copy it rather than
pointing the agent at the original so subsequent experiments start identically.
