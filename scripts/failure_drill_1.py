from __future__ import annotations

import argparse
import re
import subprocess


RUN_ID_PATTERN = re.compile(r"runs[\\\\/](?P<run_id>[a-f0-9\\-]{36})", re.IGNORECASE)


def _print_instructions() -> None:
    print("Failure Drill #1 (do not auto-run unless --execute is set)")
    print("")
    print("PowerShell:")
    print("  # Good run (dry-run)")
    print("  python -m src.main --input data/evtx_parsed --dry-run")
    print("  # Broken run (bad path)")
    print("  python -m src.main --input data/does_not_exist")
    print("  # Find the failure")
    print("  Get-Content runs/<run_id>/run_log.jsonl | Select-String \"exception\"")
    print("  Get-Content runs/<run_id>/metrics.json")
    print("")
    print("bash:")
    print("  # Good run (dry-run)")
    print("  python -m src.main --input data/evtx_parsed --dry-run")
    print("  # Broken run (bad path)")
    print("  python -m src.main --input data/does_not_exist")
    print("  # Find the failure")
    print("  grep \"exception\" runs/<run_id>/run_log.jsonl")
    print("  cat runs/<run_id>/metrics.json")


def _run_command(command: str) -> str:
    result = subprocess.run(command, shell=True, check=False, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    return output


def _extract_run_id(output: str) -> str | None:
    match = RUN_ID_PATTERN.search(output)
    if match:
        return match.group("run_id")
    return None


def _execute_drill() -> None:
    good_cmd = "python -m src.main --input data/evtx_parsed --dry-run"
    bad_cmd = "python -m src.main --input data/does_not_exist"

    print("Running good command:")
    print(f"  {good_cmd}")
    good_output = _run_command(good_cmd)
    good_run_id = _extract_run_id(good_output)
    if good_run_id:
        print(f"Good run_id: {good_run_id}")
    else:
        print("Good run_id not detected. Check output manually.")

    print("")
    print("Running broken command:")
    print(f"  {bad_cmd}")
    bad_output = _run_command(bad_cmd)
    bad_run_id = _extract_run_id(bad_output)
    if bad_run_id:
        print(f"Broken run_id: {bad_run_id}")
        print(f"Run artifacts: runs/{bad_run_id}")
        print("Inspect:")
        print(f"  runs/{bad_run_id}/run_log.jsonl")
        print(f"  runs/{bad_run_id}/metrics.json")
        print(f"  runs/{bad_run_id}/what_broke.md")
    else:
        print("Broken run_id not detected. Check output manually.")


def main() -> int:
    parser = argparse.ArgumentParser(description="PurpleLens Failure Drill #1")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the good and broken commands automatically",
    )
    args = parser.parse_args()

    _print_instructions()
    if args.execute:
        print("")
        _execute_drill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
