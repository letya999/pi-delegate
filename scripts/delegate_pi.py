#!/usr/bin/env python3
"""Run Pi or OMP once in headless mode and capture a JSON result manifest."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_duration(value: str) -> float:
    value = value.strip().lower()
    units = {"s": 1, "m": 60, "h": 3600}
    seconds = (
        float(value[:-1]) * units[value[-1]] if value[-1:] in units else float(value)
    )
    if seconds <= 0:
        raise ValueError("timeout must be greater than zero")
    return seconds


def find_runtime(runtime: str) -> str | None:
    explicit = os.environ.get("OMP_BIN" if runtime == "omp" else "PI_BIN")
    if explicit:
        return explicit
    found = shutil.which(runtime)
    if found:
        return found
    suffix = ".exe" if os.name == "nt" else ""
    candidate = Path.home() / ".bun" / "bin" / f"{runtime}{suffix}"
    return str(candidate) if candidate.is_file() else None


def run_bounded(
    command: list[str], cwd: Path, timeout: float, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    group = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        **group,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        exc.stdout, exc.stderr = stdout, stderr
        raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=("pi", "omp"), default="omp")
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--timeout", default="45m")
    parser.add_argument("--model")
    parser.add_argument("--profile")
    parser.add_argument("--agent-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--no-tools", action="store_true")
    parser.add_argument("--tools", help="Pi tool allowlist, comma-separated")
    parser.add_argument("--extension", action="append", default=[])
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--prompt-template", action="append", default=[])
    parser.add_argument("--auto-approve", action="store_true")
    args = parser.parse_args()

    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.is_dir():
        print(f"error: project directory does not exist: {cwd}", file=sys.stderr)
        return 2
    executable = find_runtime(args.runtime)
    if not executable:
        variable = "OMP_BIN" if args.runtime == "omp" else "PI_BIN"
        print(
            f"error: {args.runtime} executable not found; set {variable} or add it to PATH",
            file=sys.stderr,
        )
        return 127
    try:
        seconds = parse_duration(args.timeout)
    except ValueError as exc:
        parser.error(f"invalid --timeout: {exc}")
    if args.no_tools and args.tools:
        parser.error("--no-tools and --tools are mutually exclusive")

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else Path(tempfile.mkdtemp(prefix=f"{args.runtime}-delegate-"))
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.log"
    manifest_path = output_dir / "result.json"
    command = [executable]
    if args.runtime == "omp":
        if args.profile:
            command.extend(["--profile", args.profile])
        command.extend(
            ["--cwd", str(cwd), "--no-session", "--max-time", f"{int(seconds)}s"]
        )
    else:
        if args.profile:
            parser.error("--profile is only supported by OMP")
        # Pi uses the subprocess cwd; unlike OMP it has no --cwd or --max-time.
        command.append("--no-session")
        for option, values in (
            ("--extension", args.extension),
            ("--skill", args.skill),
            ("--prompt-template", args.prompt_template),
        ):
            for value in values:
                command.extend([option, str(Path(value).expanduser().resolve())])
        if args.tools:
            command.extend(["--tools", args.tools])
    if args.model:
        command.extend(["--model", args.model])
    if args.no_tools:
        command.append("--no-tools")
    if args.auto_approve:
        command.append("--auto-approve" if args.runtime == "omp" else "--approve")
    command.extend(["-p", args.task])
    child_env = os.environ.copy()
    if args.agent_dir:
        child_env["PI_CODING_AGENT_DIR"] = str(
            Path(args.agent_dir).expanduser().resolve()
        )

    try:
        completed = run_bounded(command, cwd, seconds + 15, child_env)
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or "", exc.stderr or ""
        exit_code, timed_out = 124, True
    except OSError as exc:
        print(f"error: could not start {args.runtime}: {exc}", file=sys.stderr)
        return 126
    else:
        stdout, stderr = completed.stdout, completed.stderr
        exit_code, timed_out = completed.returncode, False

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    response = "\n".join(
        line for line in stdout.splitlines() if line.strip() != "Working..."
    ).strip()
    manifest = {
        "tool": args.runtime,
        "cwd": str(cwd),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "response": response,
        "output_dir": str(output_dir),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))
    if timed_out:
        return 124
    if exit_code == 0 and not response:
        print(f"error: {args.runtime} produced no response", file=sys.stderr)
        return 65
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
