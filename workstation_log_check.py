import argparse
from dataclasses import dataclass
from pathlib import Path


FAIL_PATTERNS = [
    "Unknown task type",
    "Error processing:",
    "No valid BMD report to toggle",
    "Bone Age requires explicit gender override",
    "Radiology Auto-Reporter is already running. Exiting duplicate instance.",
    "Atlas PDF not found",
    "Failed to open PDF-XChange Viewer",
    "[Scan RIS] Error:",
    "[Scan RIS] Mode could not be determined",
]


@dataclass
class WorkstationLogResult:
    ok: bool
    sequence: list[str]
    failures: list[str]
    missing: list[str]


def _classify_line(line):
    lower = line.lower()
    if "processing task: dexa_toggle" in lower:
        return "dexa_toggle"
    if "processing task: dexa" in lower:
        return "dexa"
    if "processing task: bone_age" in lower:
        return "bone_age"
    return None


def check_workstation_log(text):
    sequence = []
    failures = []
    dexa_done_count = 0
    bone_age_done_count = 0
    pdf_navigation_seen = False

    for line in text.splitlines():
        event = _classify_line(line)
        if event:
            sequence.append(event)
        lower = line.lower()
        if "dexa done!" in lower:
            dexa_done_count += 1
        if "bone age done!" in lower:
            bone_age_done_count += 1
        if "pdf viewer open" in lower or "pdf viewer not open. launching directly" in lower:
            pdf_navigation_seen = True
        for pattern in FAIL_PATTERNS:
            if pattern.lower() in line.lower():
                failures.append(pattern)

    missing = []
    required_order = ["dexa", "bone_age", "dexa"]
    pos = 0
    for event in sequence:
        if pos < len(required_order) and event == required_order[pos]:
            pos += 1
    if pos < len(required_order):
        missing.append("dexa -> bone_age -> dexa sequence")

    if "dexa_toggle" not in sequence:
        missing.append("dexa_toggle")
    if dexa_done_count < 2:
        missing.append("at least two DEXA Done markers")
    if bone_age_done_count < 1:
        missing.append("Bone Age Done marker")
    if not pdf_navigation_seen:
        missing.append("Bone Age PDF navigation evidence")

    return WorkstationLogResult(
        ok=not failures and not missing,
        sequence=sequence,
        failures=failures,
        missing=missing,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check unified workstation session log evidence.")
    parser.add_argument("log_file", help="Path to a copied Show Session Log text file.")
    args = parser.parse_args(argv)

    result = check_workstation_log(Path(args.log_file).read_text(encoding="utf-8"))
    print(f"sequence={result.sequence}")
    if result.failures:
        print(f"failures={result.failures}")
    if result.missing:
        print(f"missing={result.missing}")
    print("PASS" if result.ok else "FAIL")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
