import ast
import subprocess
import sys
from pathlib import Path

import config_manager
import packaging_assets


ROOT = Path(__file__).resolve().parent

SYNTAX_FILES = [
    "main.py",
    "config_manager.py",
    "settings_ui.py",
    "setup_wizard.py",
    "ocr_engine.py",
    "capture.py",
    "output.py",
    "parser.py",
    "platform_routing.py",
    "packaging_assets.py",
    "single_instance.py",
    "workstation_log_check.py",
    "preflight_check.py",
    "modules/base.py",
    "modules/dexa.py",
    "modules/bone_age.py",
]

STALE_PATTERNS = [
    "shift+1",
    "shift+3",
    "('bone_age', None)",
    '"dexa_wb": "shift',
    '"dexa_bmd": "shift',
]

STALE_SCAN_FILES = [
    "main.py",
    "config_manager.py",
    "settings_ui.py",
    "platform_routing.py",
]


def check_syntax():
    for rel_path in SYNTAX_FILES:
        path = ROOT / rel_path
        ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)


def check_tests():
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Unit tests failed.")


def check_packaging():
    result = packaging_assets.validate_packaging_inputs(ROOT, config_manager.default_config())
    if not result["ok"]:
        raise RuntimeError(f"Packaging inputs incomplete: {result}")


def check_stale_hotkeys():
    findings = []
    for rel_path in STALE_SCAN_FILES:
        path = ROOT / rel_path
        text = path.read_text(encoding="utf-8").lower()
        for pattern in STALE_PATTERNS:
            if pattern.lower() in text:
                findings.append(f"{rel_path}: {pattern}")
    if findings:
        raise RuntimeError("Stale hotkey patterns found: " + ", ".join(findings))


def main():
    checks = [
        ("syntax", check_syntax),
        ("unit_tests", check_tests),
        ("packaging_assets", check_packaging),
        ("stale_hotkeys", check_stale_hotkeys),
    ]

    for name, fn in checks:
        print(f"[verify] {name}...")
        fn()
        print(f"[verify] {name}: PASS")

    print("[verify] unified platform checks: PASS")


if __name__ == "__main__":
    main()
