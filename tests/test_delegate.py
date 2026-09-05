"""Stdlib contract tests for the Pi / OMP delegate wrapper."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "delegate_pi.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("delegate_pi_under_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load wrapper from {SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestParseDuration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_supported_durations(self) -> None:
        self.assertEqual(self.mod.parse_duration("90s"), 90.0)
        self.assertEqual(self.mod.parse_duration("45m"), 2700.0)
        self.assertEqual(self.mod.parse_duration("2h"), 7200.0)
        self.assertEqual(self.mod.parse_duration("30"), 30.0)

    def test_rejects_non_positive_duration(self) -> None:
        for value in ("0", "-1s"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.mod.parse_duration(value)


class TestFindRuntime(unittest.TestCase):
    def test_honors_pi_bin_and_omp_bin_env(self) -> None:
        mod = _load_module()
        fake_pi = str(Path(tempfile.gettempdir()) / "fake-pi-bin.exe")
        fake_omp = str(Path(tempfile.gettempdir()) / "fake-omp-bin.exe")
        with mock.patch.dict(os.environ, {"PI_BIN": fake_pi, "OMP_BIN": fake_omp}):
            self.assertEqual(mod.find_runtime("pi"), fake_pi)
            self.assertEqual(mod.find_runtime("omp"), fake_omp)


class TestRunBounded(unittest.TestCase):
    def test_utf8_and_timeout(self) -> None:
        mod = _load_module()
        result = mod.run_bounded(
            [sys.executable, "-c", "import sys; sys.stdout.buffer.write('Привет'.encode())"],
            SKILL_ROOT,
            10,
            os.environ.copy(),
        )
        self.assertEqual(result.stdout.strip(), "Привет")
        with self.assertRaises(subprocess.TimeoutExpired):
            mod.run_bounded(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                SKILL_ROOT,
                0.1,
                os.environ.copy(),
            )


class TestMainCli(unittest.TestCase):
    def test_nonexistent_cwd_exits_2(self) -> None:
        bogus = str(Path(tempfile.gettempdir()) / "pi-delegate-no-such-cwd-xyz")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--cwd", bogus, "--task", "test"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2, msg=proc.stderr)

    def test_missing_binary_exits_127(self) -> None:
        env = os.environ.copy()
        env["PI_BIN"] = str(Path(tempfile.gettempdir()) / "missing-pi-xyz123.exe")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--runtime", "pi", "--cwd", str(SKILL_ROOT), "--task", "test"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(proc.returncode, 127, msg=(proc.stdout + proc.stderr))

    def test_pi_flags_and_successful_response(self) -> None:
        mod = _load_module()
        completed = subprocess.CompletedProcess([], 0, "Working...\nTask completed successfully", "")
        with tempfile.TemporaryDirectory() as output_dir, \
             mock.patch.object(mod, "find_runtime", return_value=sys.executable), \
             mock.patch.object(mod, "run_bounded", return_value=completed) as bounded, \
             mock.patch.object(sys, "argv", [
                 "delegate", "--runtime", "pi", "--cwd", str(SKILL_ROOT),
                 "--task", "hello", "--auto-approve", "--output-dir", output_dir
             ]):
            self.assertEqual(mod.main(), 0)
            command = bounded.call_args.args[0]
            self.assertIn("--approve", command)
            manifest = json.loads((Path(output_dir) / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["response"], "Task completed successfully")
            self.assertEqual(manifest["exit_code"], 0)

    def test_omp_flags_forwarding(self) -> None:
        mod = _load_module()
        completed = subprocess.CompletedProcess([], 0, "OMP result text", "")
        with tempfile.TemporaryDirectory() as output_dir, \
             mock.patch.object(mod, "find_runtime", return_value=sys.executable), \
             mock.patch.object(mod, "run_bounded", return_value=completed) as bounded, \
             mock.patch.object(sys, "argv", [
                 "delegate", "--runtime", "omp", "--cwd", str(SKILL_ROOT),
                 "--task", "profile-test", "--profile", "custom", "--auto-approve",
                 "--output-dir", output_dir
             ]):
            self.assertEqual(mod.main(), 0)
            command = bounded.call_args.args[0]
            self.assertIn("--profile", command)
            self.assertIn("custom", command)
            self.assertIn("--auto-approve", command)
            manifest = json.loads((Path(output_dir) / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["response"], "OMP result text")

    def test_timeout_writes_manifest(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as output_dir, \
             mock.patch.object(mod, "find_runtime", return_value=sys.executable), \
             mock.patch.object(mod, "run_bounded", side_effect=subprocess.TimeoutExpired([], 1, output=b"partial", stderr=b"timeout warning")), \
             mock.patch.object(sys, "argv", [
                 "delegate", "--runtime", "pi", "--cwd", str(SKILL_ROOT),
                 "--task", "test", "--output-dir", output_dir
             ]):
            self.assertEqual(mod.main(), 124)
            manifest = json.loads((Path(output_dir) / "result.json").read_text(encoding="utf-8"))
            self.assertEqual((manifest["tool"], manifest["exit_code"], manifest["timed_out"]), ("pi", 124, True))

    def test_empty_response_exits_65(self) -> None:
        mod = _load_module()
        completed = subprocess.CompletedProcess([], 0, "Working...\n", "")
        with tempfile.TemporaryDirectory() as output_dir, \
             mock.patch.object(mod, "find_runtime", return_value=sys.executable), \
             mock.patch.object(mod, "run_bounded", return_value=completed), \
             mock.patch.object(sys, "argv", [
                 "delegate", "--runtime", "pi", "--cwd", str(SKILL_ROOT),
                 "--task", "empty", "--output-dir", output_dir
             ]):
            self.assertEqual(mod.main(), 65)


if __name__ == "__main__":
    unittest.main()
