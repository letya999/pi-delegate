# Pi and OMP headless reference

This skill provides unified headless execution for both the Pi Coding Agent and Oh My Pi (OMP):

## Pi Runtime (`--runtime pi`)
- Headless invocation: `pi -p "<task>"`
- Working directory: Subprocess cwd (Pi native behavior)
- Session isolation: `--no-session`
- Approval: `--approve` (passed when `--auto-approve` is requested)
- Tool control: `--no-tools` or `--tools <allowlist>` (e.g. `read,grep,find,ls,write`)
- Extensions & Templates: `--extension <path>`, `--skill <path>`, `--prompt-template <path>`
- Agent Home / Auth: `--agent-dir <path>` sets `PI_CODING_AGENT_DIR`

## Oh My Pi Runtime (`--runtime omp`)
- Headless invocation: `omp -p "<task>"`
- Working directory: `--cwd <path>`
- Session isolation: `--no-session`
- Timeout flag: `--max-time <seconds>s`
- Profile: `--profile <name>`
- Approval: `--auto-approve` (passed when `--auto-approve` is requested)

## Authentication & Credentials
Authentication is expected to be preconfigured through the user's Pi or OMP login/profile. Never read, print, or pass OAuth tokens or API keys on command lines. If authentication fails, report the CLI error directly and instruct the user to authenticate outside this wrapper.
