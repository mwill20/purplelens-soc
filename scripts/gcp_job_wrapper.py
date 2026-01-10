from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.cloud import storage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cloud Run Jobs wrapper for PurpleLens batch analysis."
    )
    parser.add_argument(
        "--input-gcs",
        required=True,
        help="GCS URI to a file or prefix (e.g., gs://bucket/inputs/sample.jsonl).",
    )
    parser.add_argument(
        "--output-gcs",
        required=True,
        help="GCS URI prefix for outputs (e.g., gs://bucket/outputs).",
    )
    parser.add_argument(
        "--source",
        choices=["auto", "windows", "aws", "gcp"],
        default=os.getenv("SOURCE", "auto"),
        help="Source type for analysis (default: auto).",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "gemini"],
        default=os.getenv("PROVIDER", "gemini"),
        help="LLM provider (default: gemini).",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("MODEL", "gemini-flash-latest"),
        help="LLM model (default: gemini-flash-latest).",
    )
    parser.add_argument(
        "--db",
        default=os.getenv("DB_PATH", "db/analysis.db"),
        help="SQLite DB path (default: db/analysis.db).",
    )
    parser.add_argument(
        "--run-tag",
        default=os.getenv("RUN_TAG"),
        help="Optional run tag for output folder naming.",
    )
    parser.add_argument(
        "--upload-logs",
        action="store_true",
        help="Upload logs to GCS after completion.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs only, do not call LLM.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def _parse_gcs_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {uri}")
    bucket_and_path = uri[5:]
    bucket, _, path = bucket_and_path.partition("/")
    return bucket, path


def _normalize_prefix(path: str) -> str:
    if path and not path.endswith("/"):
        return f"{path}/"
    return path


def _download_prefix(
    client: storage.Client,
    bucket_name: str,
    prefix: str,
    destination: Path,
) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    for blob in client.list_blobs(bucket_name, prefix=prefix):
        if blob.name.endswith("/"):
            continue
        relative = blob.name[len(prefix) :] if prefix else blob.name
        relative = relative.lstrip("/")
        local_path = destination / relative
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
        downloaded += 1
    if downloaded == 0:
        raise FileNotFoundError(
            f"No objects found with prefix gs://{bucket_name}/{prefix}"
        )
    return destination


def download_input(
    client: storage.Client,
    input_gcs: str,
    workspace: Path,
) -> Path:
    bucket_name, object_path = _parse_gcs_uri(input_gcs)
    if not object_path:
        raise ValueError("input-gcs must include an object path or prefix.")
    bucket = client.bucket(bucket_name)

    if not object_path or object_path.endswith("/"):
        input_dir = workspace / "inputs"
        return _download_prefix(client, bucket_name, object_path, input_dir)

    blob = bucket.blob(object_path)
    if blob.exists():
        input_dir = workspace / "inputs"
        input_dir.mkdir(parents=True, exist_ok=True)
        local_path = input_dir / Path(object_path).name
        blob.download_to_filename(str(local_path))
        return local_path

    input_dir = workspace / "inputs"
    return _download_prefix(client, bucket_name, object_path, input_dir)


def _upload_file(
    client: storage.Client,
    bucket_name: str,
    destination_path: str,
    local_path: Path,
) -> None:
    blob = client.bucket(bucket_name).blob(destination_path)
    blob.upload_from_filename(str(local_path))


def upload_outputs(
    client: storage.Client,
    output_gcs: str,
    repo_root: Path,
    db_path: Path,
    upload_logs: bool,
    run_tag: str,
    min_mtime: float | None,
) -> None:
    bucket_name, prefix = _parse_gcs_uri(output_gcs)
    prefix = _normalize_prefix(prefix)
    output_root = f"{prefix}runs/{run_tag}/"

    reports_dir = repo_root / "reports"
    if reports_dir.exists():
        for report in reports_dir.glob("analysis_*.txt"):
            if min_mtime and report.stat().st_mtime < min_mtime:
                continue
            _upload_file(
                client,
                bucket_name,
                f"{output_root}reports/{report.name}",
                report,
            )

    if db_path.exists() and (not min_mtime or db_path.stat().st_mtime >= min_mtime):
        _upload_file(
            client,
            bucket_name,
            f"{output_root}db/{db_path.name}",
            db_path,
        )

    if upload_logs:
        logs_dir = repo_root / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.glob("run_*.log"):
                if min_mtime and log_file.stat().st_mtime < min_mtime:
                    continue
                _upload_file(
                    client,
                    bucket_name,
                    f"{output_root}logs/{log_file.name}",
                    log_file,
                )


def run_cli(repo_root: Path, args: argparse.Namespace, input_path: Path) -> int:
    cmd = [
        sys.executable,
        "src/main.py",
        "--input",
        str(input_path),
        "--source",
        args.source,
        "--output",
        "file",
        "--model",
        args.model,
        "--provider",
        args.provider,
        "--db",
        args.db,
    ]
    if args.verbose:
        cmd.append("--verbose")
    if args.debug:
        cmd.append("--debug")
    if args.dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, cwd=repo_root, check=False)
    return result.returncode


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    workspace = repo_root / "job_workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    client = storage.Client()
    input_path = download_input(client, args.input_gcs, workspace)

    run_started_at = datetime.now(timezone.utc)
    run_tag = args.run_tag or run_started_at.strftime("%Y%m%dT%H%M%SZ")
    exit_code = run_cli(repo_root, args, input_path)

    db_path = Path(args.db)
    if not db_path.is_absolute():
        db_path = repo_root / db_path

    upload_outputs(
        client=client,
        output_gcs=args.output_gcs,
        repo_root=repo_root,
        db_path=db_path,
        upload_logs=args.upload_logs,
        run_tag=run_tag,
        min_mtime=run_started_at.timestamp(),
    )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
