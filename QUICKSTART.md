# Pi & OMP Delegate Quickstart

Use this skill when the caller explicitly wants Pi Coding Agent or Oh My Pi (OMP) to run as a separate headless agent.

## Requirements

- Python 3.10+
- Pi or OMP CLI on `PATH`, or `PI_BIN` / `OMP_BIN` set to the executable path
- Authentication already configured by the user

## Run

POSIX shell on macOS, Linux, or WSL:

```sh
python3 scripts/delegate_pi.py \
  --runtime pi \
  --cwd "$PWD" \
  --task "Review this repository and report the highest-risk issue." \
  --timeout 45m
```

Windows PowerShell:

```powershell
py -3 .\scripts\delegate_pi.py `
  --runtime pi `
  --cwd (Get-Location).Path `
  --task "Review this repository and report the highest-risk issue." `
  --timeout 45m
```

For Oh My Pi (OMP):

```powershell
py -3 .\scripts\delegate_pi.py `
  --runtime omp `
  --cwd (Get-Location).Path `
  --task "Report project health." `
  --timeout 10m
```

## Result

The wrapper prints a JSON manifest with `response`, `exit_code`, `stdout`, `stderr`, and `output_dir`. Treat the answer as unverified until the controlling agent checks diffs and tests.
