import os

REPORTS_DIR = "reports"

PATTERNS = {
    "GCP": [
        "gcp",
        "google",
        "cloud storage",
        "storage.setiampolicy",
        "setiampolicy",
        "cloud functions",
    ],
    "AWS": ["aws", "cloudtrail", "s3", "kms", "cloudwatch"],
    "EVTX": ["evtx", "winlog", "windows", "eventid", "winlogbeat"],
}


def classify_snippet(snippet: str):
    s = snippet.lower()
    for cat, pats in PATTERNS.items():
        for p in pats:
            if p in s:
                return cat
    return None


def main():
    if not os.path.isdir(REPORTS_DIR):
        print(f"No '{REPORTS_DIR}' directory found. Nothing to prune.")
        return

    files_by_cat = {"GCP": [], "AWS": [], "EVTX": []}

    for name in os.listdir(REPORTS_DIR):
        path = os.path.join(REPORTS_DIR, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                data = fh.read(8192)
        except Exception:
            data = ""
        cat = classify_snippet(data)
        if cat in files_by_cat:
            files_by_cat[cat].append((os.path.getmtime(path), path))

    total_removed = 0
    for cat, entries in files_by_cat.items():
        if len(entries) <= 1:
            print(f"{cat}: {len(entries)} file(s) found — nothing to remove.")
            continue
        entries.sort(reverse=True)
        keep = entries[0][1]
        to_remove = [p for (_, p) in entries[1:]]
        for p in to_remove:
            try:
                os.remove(p)
                print(f"Removed {p} (kept {keep})")
                total_removed += 1
            except Exception as e:
                print(f"Failed to remove {p}: {e}")
    print(f"Prune complete. Removed {total_removed} file(s).")


if __name__ == "__main__":
    main()
