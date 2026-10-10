from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "well_check" / "well_check.py"
REQUIREMENTS = ROOT / "well_check" / "requirements.txt"


class WellStdlibRuntimeTests(unittest.TestCase):
    def test_checker_runs_with_site_packages_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "good.md"
            artifact.write_text(
                "The checker is portable because its runtime uses only the Python standard library.\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, "-S", str(CHECKER), str(artifact)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "PASS")

    def test_requirements_file_has_no_installable_dependencies(self) -> None:
        installable = [
            line.strip()
            for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(installable, [])

    def test_script_declares_stdlib_only_runtime(self) -> None:
        spec = importlib.util.spec_from_file_location("well_check_stdlib_test", CHECKER)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        self.assertEqual(
            module.RUNTIME_REQUIREMENT,
            "Python 3.9+ standard library only; no third-party dependencies",
        )
        source = CHECKER.read_text(encoding="utf-8")
        self.assertNotIn("markdown_it", source)
        self.assertNotIn("mdit_py_plugins", source)


if __name__ == "__main__":
    unittest.main()
