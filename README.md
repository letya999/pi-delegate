<p align="center">
  <strong>English</strong> · <a href="README.ru.md">Русский</a>
</p>

<p align="center">
  <h1 align="center">Pi Delegate</h1>
</p>

<p align="center">
  <a href="https://github.com/letya999/pi-delegate-skill"><img src="https://img.shields.io/badge/status-active-brightgreen" alt="status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT"></a>
  <a href="https://skills.sh/letya999/pi-delegate-skill"><img src="https://skills.sh/b/letya999/pi-delegate-skill" alt="skills.sh"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/cli-pi%20%7C%20omp-purple" alt="CLI: pi | omp">
</p>

Headless Pi Coding Agent and Oh My Pi (OMP) delegate skill by [Artem Letyushev](https://github.com/letya999).

The command is `scripts/delegate_pi.py`. The primary consumer is the controlling agent or orchestrator: every execution runs Pi or OMP once as a bounded, non-interactive subprocess and returns one structured JSON envelope.

---

## One objective, bounded subprocess, zero trust

The wrapper acts as a deterministic isolation layer between your controlling agent and the Pi/OMP CLI:

- **Dual runtime support:** Seamlessly delegates to either native Pi (`--runtime pi`) or Oh My Pi (`--runtime omp`).
- **Single non-interactive execution:** Invokes CLI directly via `subprocess.run(..., shell=False)` without terminal takeovers.
- **Granular tool control:** Supports explicit Pi tool allowlists (`--tools read,grep,find,ls,write`) or complete tool disabling (`--no-tools`).
- **Zero-trust verification:** Outputs are unverified until independently confirmed by diffs and tests.
- **Credential isolation:** Never copies or logs authentication tokens between user homes and experimental harnesses.

## Capability matrix

| Capability / Setting | Specification | Behavior & Guarantees |
|---|---|---|
| **Runtimes** | `--runtime pi` or `--runtime omp` | Unified interface for both Pi Coding Agent and Oh My Pi |
| **Headless command** | `pi -p "<task>"` / `omp -p "<task>"` | Non-interactive execution in print mode |
| **Workspace scoping** | Subprocess cwd (Pi) / `--cwd <cwd>` (OMP) | Restricts agent to the target project working directory |
| **Tool restrictions** | `--tools <list>` or `--no-tools` | Controls tool permissions granted to the agent |
| **Extensions & Skills** | `--extension`, `--skill`, `--prompt-template` | Forwards external resources cleanly into the execution context |
| **OMP profiles** | `--profile <name>` | Selects existing Oh My Pi profile (OMP runtime only) |
| **Isolated agent home** | `--agent-dir <path>` | Sets `PI_CODING_AGENT_DIR` without credential copying |
| **Autonomous edits** | `--auto-approve` | Passes `--approve` (Pi) or `--auto-approve` (OMP) |
| **Executable override** | `PI_BIN` / `OMP_BIN` env vars | Custom executable path before searching PATH and Bun |
| **Standard exit codes** | `0, 2, 65, 124, 126, 127` | Standardized error signaling |

## Install

With `npx skills`:

```bash
npx skills add letya999/pi-delegate-skill
```

Or clone into an agent skill directory:

```bash
git clone https://github.com/letya999/pi-delegate-skill.git .agents/skills/pi-delegate
```

## Quick Start

### POSIX (macOS, Linux, WSL)

```bash
python3 scripts/delegate_pi.py \
  --runtime pi \
  --cwd "$PWD" \
  --task "Review this repository and report the highest-risk issue." \
  --timeout 45m
```

### Windows PowerShell

```powershell
py -3 .\scripts\delegate_pi.py `
  --runtime pi `
  --cwd (Get-Location).Path `
  --task "Review this repository and report the highest-risk issue." `
  --timeout 45m
```

---

<details>
<summary>JSON Manifest Schema & Agent Integration</summary>

The wrapper writes `stdout.txt`, `stderr.log`, and `result.json` into a temporary directory:

```json
{
  "tool": "pi",
  "cwd": "C:\\work\\repo",
  "exit_code": 0,
  "timed_out": false,
  "response": "Clean extracted response text from Pi/OMP",
  "output_dir": "C:\\Temp\\pi-delegate-xyz",
  "stdout": "C:\\Temp\\pi-delegate-xyz\\stdout.txt",
  "stderr": "C:\\Temp\\pi-delegate-xyz\\stderr.log"
}
```

If the execution completes with exit code 0 but returns an empty response, the wrapper returns code `65`.

</details>

<details>
<summary>CLI Flags & Configuration Reference</summary>

| Flag | Type | Description |
|---|---|---|
| `--runtime` | `pi` or `omp` (default: `omp`) | Target CLI runtime to execute. |
| `--cwd` | Path (required) | Target project directory. Exits with `2` if missing. |
| `--task` | String (required) | Delegated instruction / task for Pi/OMP. |
| `--timeout` | Duration (default: `45m`) | Timeout formatted as `90s`, `45m`, `2h`, or integer seconds. |
| `--model` | String | Model override string. |
| `--profile` | String | OMP profile name (OMP runtime only). |
| `--agent-dir` | Path | Custom Pi config directory (`PI_CODING_AGENT_DIR`). |
| `--tools` | String | Tool allowlist (e.g. `read,grep,find,ls,write`). |
| `--no-tools` | Flag | Disables all tool invocations. |
| `--extension` | Path (repeatable) | Extension path forwarded to Pi. |
| `--skill` | Path (repeatable) | Skill path forwarded to Pi. |
| `--prompt-template` | Path (repeatable) | Prompt template forwarded to Pi. |
| `--auto-approve` | Flag | Auto-approves tool execution. |
| `--output-dir` | Path | Custom artifact directory. |

</details>

<details>
<summary>Safety Posture & Credential Guardrails</summary>

- **No credential leaks:** Never reads, prints, or copies OAuth tokens or API keys between user profiles.
- **Explicit tool allowlists:** Supports restricting tools to read-only sets when full access is not authorized.
- **Anti-recursion rule:** Delegated instances must not recursively spawn further delegate wrappers.

</details>

<details>
<summary>Independent Verification Protocol</summary>

Outputs are unverified evidence. After delegated file modifications:

1. Check changes independently: `git diff --stat` and `git diff`.
2. Run test suites outside the delegated environment: `pytest`, `npm test`, etc.
3. Verify newly generated files and imports.

</details>

<details>
<summary>Test Suite & Quality Checks</summary>

Run the test suite with standard library `unittest`:

```bash
python -m unittest discover -s tests -v
```

</details>

<details>
<summary>Agent Skill Entry Points</summary>

- [SKILL.md](SKILL.md) — Skill instruction specification for coding agents.
- [QUICKSTART.md](QUICKSTART.md) — Quick command reference.
- [references/runtime-setup.md](references/runtime-setup.md) — Cross-platform pre-flight checks.
- [references/headless-reference.md](references/headless-reference.md) — Pi/OMP CLI headless reference.
- [.well-known/agent-skills/index.json](.well-known/agent-skills/index.json) — Discovery index for skills.sh.
- [dist/pi-delegate.zip](dist/pi-delegate.zip) — Discoverable archive artifact.

</details>

<details>
<summary>License</summary>

MIT License. See [LICENSE](LICENSE) for full text. Copyright (c) 2026 Artem Letyushev.

</details>
