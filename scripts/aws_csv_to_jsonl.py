"""Convert Kaggle CloudTrail CSV to JSONL for PurpleLens ingestion."""

from __future__ import annotations

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

CSV_TO_CLOUDTRAIL_MAPPING = {
    # Core event identity
    "eventID": "eventID",
    "eventTime": "eventTime",
    "eventVersion": "eventVersion",
    "eventType": "eventType",
    "eventName": "eventName",
    "eventSource": "eventSource",
    "awsRegion": "awsRegion",
    "apiVersion": "apiVersion",
    # Outcome & classification
    "errorCode": "errorCode",
    "errorMessage": "errorMessage",
    "readOnly": "readOnly",
    "managementEvent": "managementEvent",
    # Network & origin
    "sourceIPAddress": "sourceIPAddress",
    "userAgent": "userAgent",
    "vpcEndpointId": "vpcEndpointId",
    # Base identity
    "userIdentitytype": "userIdentity.type",
    "userIdentityaccountId": "userIdentity.accountId",
    "recipientAccountId": "recipientAccountId",
    "userIdentityprincipalId": "userIdentity.principalId",
    "userIdentityarn": "userIdentity.arn",
    "userIdentityuserName": "userIdentity.userName",
    "userIdentityaccessKeyId": "userIdentity.accessKeyId",
    "userIdentityinvokedBy": "userIdentity.invokedBy",
    # Assumed role / session context
    "sessionIssuerArn": "userIdentity.sessionContext.sessionIssuer.arn",
    "sessionIssuerUserName": "userIdentity.sessionContext.sessionIssuer.userName",
    "sessionMfaAuthenticated": "userIdentity.sessionContext.attributes.mfaAuthenticated",
    "sessionCreationDate": "userIdentity.sessionContext.attributes.creationDate",
    # Request/response analysis
    "requestParameters": "requestParameters",
    "responseElements": "responseElements",
    "additionalEventData": "additionalEventData",
    # Organizational correlation
    "sharedEventID": "sharedEventID",
}

REQUIRED_FIELDS = ["eventTime", "eventSource", "eventName"]


def _set_nested_value(target: Dict[str, Any], dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    current = target
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _build_cloudtrail_record(row: Dict[str, Any]) -> Dict[str, Any]:
    record: Dict[str, Any] = {}
    for csv_key, json_path in CSV_TO_CLOUDTRAIL_MAPPING.items():
        value = row.get(csv_key)
        if value is None or value == "":
            continue
        _set_nested_value(record, json_path, value)
    return record


def convert_csv_to_jsonl(input_path: Path, output_path: Path) -> Dict[str, int]:
    total_rows = 0
    converted_rows = 0
    skipped_rows = 0

    with input_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV input has no headers.")

        with output_path.open("w", encoding="utf-8") as output:
            for row_index, row in enumerate(reader, start=1):
                total_rows += 1
                missing = [field for field in REQUIRED_FIELDS if not row.get(field)]
                if missing:
                    skipped_rows += 1
                    logger.warning(
                        "Skipping row %d missing required fields: %s",
                        row_index,
                        ", ".join(missing),
                    )
                    continue

                record = _build_cloudtrail_record(row)
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
                converted_rows += 1

    return {
        "rows_read": total_rows,
        "rows_converted": converted_rows,
        "rows_skipped": skipped_rows,
    }


def _main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if len(sys.argv) != 3:
        print("Usage: python scripts/aws_csv_to_jsonl.py <input_csv> <output_jsonl>")
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Input CSV not found: {input_path}")
        return 1

    stats = convert_csv_to_jsonl(input_path, output_path)
    print(
        "Conversion complete: "
        f"{stats['rows_read']} rows read, "
        f"{stats['rows_converted']} converted, "
        f"{stats['rows_skipped']} skipped."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
