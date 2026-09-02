---
name: pi-delegate
description: Run Pi Coding Agent or Oh My Pi (OMP) as a bounded headless delegate. Use when the user asks to delegate to Pi/OMP, test a Pi setup through a real model, or obtain a Pi-backed second opinion. Do not use for interactive sessions or unrelated CLIs.
---

# Pi Delegate

Run Pi or OMP once in non-interactive print mode and return the captured result.

## Workflow

1. Resolve the project directory and confirm it exists.
2. Choose the runtime named by the user. Use `--runtime pi` for ordinary Pi; use `--runtime omp` only for OMP.
3. Use `scripts/delegate_pi.py`. Pass `--profile` only for an existing OMP profile. For Pi, `--agent-dir` selects the complete Pi config/auth directory; use it for an experiment target only when that directory is already authenticated. The wrapper never copies credentials between the normal Pi home and a target.
4. Keep normal tool approval by default. Add `--auto-approve` only for an authorized task in a trusted directory. For an observer that may write only its separate state YAML, use a Pi `--tools` allowlist such as `read,grep,find,ls,write`; use `--no-tools` only when no inspection is needed.
5. Report the response, exit status, runtime, and output directory. If files may have changed, inspect the diff and verify independently.

## Invariants

- Authentication comes from the selected Pi/OMP installation or profile. Never read, print, copy, or pass OAuth tokens and API keys.
- Invoke the executable directly, never through a shell. The wrapper uses `OMP_BIN` or `PI_BIN` for an explicit executable and otherwise checks PATH plus the usual Bun bin directory.
- Pi receives its working directory through the subprocess cwd and uses Pi-native flags (`--no-session`, `--approve`); OMP receives its own `--cwd`, `--max-time`, and approval flags.
- Pi-only `--extension`, `--skill`, and `--prompt-template` pass explicit provider-managed resources into a new context while keeping authentication in the selected normal Pi profile. This is useful when a provider target is not itself authenticated.
- Always use a finite timeout. A timeout terminates the process tree and returns exit code 124.
- The wrapper writes stdout, stderr, and `result.json`, then prints one JSON manifest. A zero exit with an empty response is a failure.
- Treat the delegate response as evidence, not proof. For setup experiments, require filesystem/provider evidence plus install and rollback results.

## Example

```powershell
py scripts/delegate_pi.py --runtime pi --cwd C:\work\project --timeout 3m --task "Report the active experiment marker."
```
