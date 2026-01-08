# 📥 **Lesson 03: Phase 1 Deep Dive - Ingest (Loading Events)**

This lesson takes you inside [src/ingest.py](../src/ingest.py) - the first phase of the pipeline that loads Windows event logs and attaches provenance tracking.

---

## **🎯 Learning Goals**

By the end of this lesson, you'll be able to:
- ✅ Explain what "ingest" means and why it's Phase 1
- ✅ Read and understand the `load_events()` function line-by-line
- ✅ Trace how one JSONL line becomes a Python dictionary
- ✅ Explain provenance metadata (`source_file`, `record_index`, `event_id`)
- ✅ Understand error handling for malformed JSON
- ✅ Test the ingestion phase manually

---

## **📚 Key Concepts**

### **What Does "Ingest" Mean?**

**In plain English:** Ingest = Load data into the system

Think of it like **intake** at a hospital:
- Patients arrive (raw data files)
- Intake clerk records: Name, ID number, when they arrived (provenance)
- Patients enter the system with proper tracking

**In this project:**
- JSONL files arrive in `data/evtx_parsed/`
- Ingest attaches: source file, line number, event ID (provenance)
- Events enter the pipeline with proper tracking

### **Why Provenance Matters**

**Provenance** = Proof of where data came from (chain of custody for digital evidence)

When the system finds suspicious activity, you need to answer:
- 📁 Which file was this in? → `source_file`
- 📍 Which line number? → `record_index`
- 🔍 What Event ID? → `event_id`

This lets you:
1. Verify findings by checking the original log
2. Cite sources in your report (like footnotes)
3. Trace back to raw `.evtx` files if needed

---

## **🔍 The Code: Opening src/ingest.py**

Let's read [src/ingest.py](../src/ingest.py) together. Open it in VS Code.

### **Step 1: Imports (Lines 1-7)**

```python
"""Event log ingestion with provenance tracking."""

import json
import logging
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)
```

**What's happening:**
- `json` - Python's built-in library for reading JSON
- `logging` - For writing info/warning/error messages
- `pathlib.Path` - Modern way to work with file paths (better than strings)
- `typing.List` - Type hint (tells Python this returns a list)

**Technical term:** `LOGGER = logging.getLogger(__name__)` creates a logger that identifies messages as coming from "src.ingest"

---

### **Step 2: Constants (Lines 9-11)**

```python
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
```

**What's happening:**
- Sets a safety limit: Don't load files bigger than 10 MB
- `1024 * 1024` = 1 MB (in bytes)
- `10 * 1024 * 1024` = 10 MB

**Why this limit?**
- Prevents memory issues if someone tries to load a 2 GB file
- Forces you to split huge logs into smaller chunks
- Reasonable for demo/testing (production might increase this)

---

### **Step 3: The Main Function - `load_events()` (Lines 14-55)**

This is the heart of Phase 1. Let's read it section by section:

#### **Part A: Setup and Validation (Lines 14-21)**

```python
def load_events(input_dir: str) -> List[dict]:
    """
    Load all .jsonl files from a directory and attach provenance metadata.
    
    Args:
        input_dir: Path to directory containing .jsonl files
        
    Returns:
        List of event dictionaries with provenance fields added
        
    Raises:
        FileNotFoundError: If directory is empty or no .jsonl files found
    """
    input_path = Path(input_dir)
    jsonl_files = sorted(input_path.glob("*.jsonl"))
    
    if not jsonl_files:
        msg = f"No JSONL files found in {input_dir}. Please run prep_evtx.ps1 first."
        LOGGER.error(msg)
        raise FileNotFoundError(msg)
```

**Breaking it down:**

**Line 14:** Function signature
- `input_dir: str` = Takes a directory path as a string
- `-> List[dict]` = Returns a list of dictionaries (type hint)

**Lines 15-23:** Docstring (the multi-line comment in `"""`)
- Explains what the function does
- Documents parameters and return value
- Lists possible errors

**Line 24:** `input_path = Path(input_dir)`
- Converts the string path to a `Path` object
- Now we can use methods like `.glob()` and `.read_text()`

**Line 25:** `jsonl_files = sorted(input_path.glob("*.jsonl"))`
- `glob("*.jsonl")` = Find all files ending in `.jsonl`
- `sorted()` = Put them in alphabetical order (predictable processing)
- Returns a list like: `[Path('Credential_hashdump.jsonl'), Path('Execution_wmic.jsonl'), ...]`

**Lines 27-30:** Error handling
- If no files found, log an error and raise `FileNotFoundError`
- The error message tells you what to do: "run prep_evtx.ps1 first"

---

#### **Part B: File Size Validation (Lines 32-35)**

```python
    for filepath in jsonl_files:
        file_size = filepath.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            msg = f"File {filepath.name} exceeds {MAX_FILE_SIZE_BYTES} bytes"
            LOGGER.error(msg)
            raise ValueError(msg)
```

**What's happening:**
- Loop through each file
- `filepath.stat().st_size` = Get file size in bytes
- If bigger than 10 MB, log error and raise `ValueError`

**Why check size before loading?**
- Prevent trying to load a 2 GB file into memory (would crash)
- Fail fast with a clear error message

---

#### **Part C: Main Loading Loop (Lines 37-55)**

```python
    events = []
    LOGGER.info("Loading events from %d files", len(jsonl_files))
    
    for filepath in jsonl_files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as exc:
            LOGGER.error("Failed to read %s: %s", filepath.name, exc)
            continue
        
        for line_idx, line in enumerate(content.splitlines()):
            line = line.strip()
            if not line:
                continue
            
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                LOGGER.warning(
                    "Skipping malformed JSON in %s at line %d: %s",
                    filepath.name,
                    line_idx + 1,
                    exc,
                )
                continue
            
            # Attach provenance metadata
            event["source_file"] = filepath.name
            event["record_index"] = line_idx
            event["event_id"] = _extract_event_id(event)
            events.append(event)
    
    LOGGER.info("Loaded %d events from %d files", len(events), len(jsonl_files))
    return events
```

**Let's trace what happens to ONE line:**

1. **Line 43-48:** Read the file
   ```python
   content = filepath.read_text(encoding="utf-8")
   ```
   - Reads entire file as one big string
   - `encoding="utf-8"` ensures special characters work
   - Wrapped in `try/except` to catch read errors

2. **Line 50:** Split into lines
   ```python
   for line_idx, line in enumerate(content.splitlines()):
   ```
   - `splitlines()` = Break the string at newlines (`\n`)
   - `enumerate()` = Gives us both the index (0, 1, 2...) and the line content
   - `line_idx` will be 0 for first line, 1 for second, etc.

3. **Lines 51-53:** Skip blank lines
   ```python
   line = line.strip()  # Remove whitespace
   if not line:          # If empty
       continue          # Skip to next line
   ```

4. **Lines 55-63:** Parse JSON
   ```python
   try:
       event = json.loads(line)  # Parse JSON string → Python dict
   except json.JSONDecodeError as exc:
       LOGGER.warning("Skipping malformed JSON...")
       continue
   ```
   - `json.loads(line)` = Convert JSON string to Python dictionary
   - If the JSON is malformed (missing bracket, extra comma, etc.), log a warning and skip it
   - **Graceful degradation** = Don't crash, just skip bad lines

5. **Lines 65-68:** Attach provenance
   ```python
   event["source_file"] = filepath.name        # "Credential_hashdump.jsonl"
   event["record_index"] = line_idx            # 0, 1, 2, etc.
   event["event_id"] = _extract_event_id(event)  # "4688", "4624", etc.
   events.append(event)
   ```
   - Add three new fields to the dictionary
   - These fields start with `_` to show they're metadata (not original event data)
   - Append to the `events` list

6. **Lines 70-71:** Log summary and return
   ```python
   LOGGER.info("Loaded %d events from %d files", len(events), len(jsonl_files))
   return events
   ```

---

### **Step 4: Helper Function - `_extract_event_id()` (Lines 58-71)**

```python
def _extract_event_id(event: dict) -> str | None:
    """
    Extract Windows Event ID from event structure.
    
    Args:
        event: Event dictionary
        
    Returns:
        Event ID as string, or None if not found
    """
    try:
        # Try Windows Event Log structure
        if "Event" in event and "System" in event["Event"]:
            event_id = event["Event"]["System"].get("EventID")
            return str(event_id) if event_id is not None else None
        return None
    except (KeyError, TypeError, AttributeError):
        return None
```

**What's happening:**
- Navigates the nested JSON structure to find the Event ID
- Windows event logs have structure: `{"Event": {"System": {"EventID": 4688}}}`
- Returns the ID as a string (e.g., `"4688"`)
- If structure doesn't match or ID missing, returns `None`
- The `_` prefix means "private helper function" (only used internally)

**Why convert to string?**
- Some Event IDs might not be numbers
- Strings are safer for storage and comparison
- Consistent data type (not mixing ints and strings)

---

## **📊 Visual: What Happens During Ingest**

```
INPUT: data/evtx_parsed/Credential_hashdump.jsonl
─────────────────────────────────────────────────
Line 0: {"Event":{"System":{"EventID":4656},...}}
Line 1: {"Event":{"System":{"EventID":4663},...}}

               ↓ load_events() processes ↓

STEP 1: glob("*.jsonl") finds files
  → [Credential_hashdump.jsonl, Execution_wmic.jsonl, Lateral_wmic.jsonl]

STEP 2: For each file, read_text() loads content

STEP 3: splitlines() breaks into individual lines

STEP 4: For each line:
  - json.loads() parses JSON → Python dict
  - Add source_file: "Credential_hashdump.jsonl"
  - Add record_index: 0, 1, 2, etc.
  - Add event_id: "4656", "4663", etc.
  - Append to events list

STEP 5: Return events list

OUTPUT: List of 15 event dictionaries with provenance
─────────────────────────────────────────────────────
[
  {
    "Event": {"System": {"EventID": 4656}, ...},
    "source_file": "Credential_hashdump.jsonl",
    "record_index": 0,
    "_event_id": "4656"
  },
  {
    "Event": {"System": {"EventID": 4663}, ...},
    "_source_file": "Credential_hashdump.jsonl",
    "_record_index": 1,
    "_event_id": "4663"
  },
  ...
]
```

---

## **🧪 Hands-On Exercise: Test Ingestion Manually**

Let's run the ingest phase by itself to see it work!

### **Exercise 1: Load Events and Print Summary**

Open a Python interactive shell in your project directory:

```powershell
# Activate virtual environment
.venv\Scripts\Activate

# Start Python shell
python
```

Then run this code:

```python
from src.ingest import load_events

# Load events
events = load_events("data/evtx_parsed")

# Print summary
print(f"Loaded {len(events)} total events")

# Show files found
sources = set(e["source_file"] for e in events)
print(f"From {len(sources)} files: {sources}")

# Show Event ID breakdown
from collections import Counter
event_ids = Counter(e["event_id"] for e in events)
print(f"Event ID distribution: {dict(event_ids)}")

# Look at first event
print("\nFirst event structure:")
import json
print(json.dumps(events[0], indent=2))
```

**Expected output:**
```
Loaded 15 total events
From 3 files: {'Credential_hashdump.jsonl', 'Execution_wmic.jsonl', 'Lateral_wmic.jsonl'}
Event ID distribution: {'4656': 2, '4663': 2, '1': 8, '4688': 2, '4648': 1}

First event structure:
{
  "Event": {
    "System": {
      "EventID": 4656,
      ...
    }
  },
  "source_file": "Credential_hashdump.jsonl",
  "record_index": 0,
  "event_id": "4656"
}
```

---

### **Exercise 2: Test Error Handling - Empty Directory**

```python
from src.ingest import load_events

try:
    events = load_events("data/empty_folder")
except FileNotFoundError as e:
    print(f"Caught expected error: {e}")
```

**Expected output:**
```
Caught expected error: No JSONL files found in data/empty_folder. Please run prep_evtx.ps1 first.
```

---

### **Exercise 3: Test Malformed JSON Handling**

Create a test file with bad JSON:

```powershell
# Create test directory
New-Item -ItemType Directory -Path "test_ingest" -Force

# Create file with one good line and one bad line
@"
{"Event":{"System":{"EventID":1234}}}
{this is not valid JSON!!!}
{"Event":{"System":{"EventID":5678}}}
"@ | Out-File -FilePath "test_ingest\test.jsonl" -Encoding UTF8
```

Then test it:

```python
from src.ingest import load_events

events = load_events("test_ingest")
print(f"Loaded {len(events)} events (should be 2, skipping the malformed line)")

# Check you see the warning in the logs
```

**Expected behavior:**
- Logs a warning: `"Skipping malformed JSON in test.jsonl at line 2"`
- Continues processing
- Returns 2 events (the valid ones)
- **Graceful degradation** = doesn't crash on bad data

---

## **🎯 Key Takeaways**

### **What Ingest Does:**
1. ✅ Scans directory for `.jsonl` files
2. ✅ Validates file sizes (< 10 MB)
3. ✅ Reads each file line-by-line
4. ✅ Parses JSON (skips malformed lines)
5. ✅ Attaches provenance metadata
6. ✅ Returns list of enriched events

### **Why Provenance is Critical:**
- **Traceability**: Can verify findings by checking original logs
- **Citation**: Reports can reference exact source and line number
- **Debugging**: If something looks wrong, trace back to source
- **Audit Trail**: Proves you didn't fabricate evidence

### **Error Handling Philosophy:**
- **Fail fast** on missing directory (can't proceed)
- **Fail fast** on oversized files (safety limit)
- **Graceful degradation** on malformed JSON (skip and continue)
- Always log errors/warnings so analysts know what happened

---

## **💬 Interview Talking Points**

### **"Walk me through how ingestion works"**

> "Ingestion is Phase 1 of the pipeline. The `load_events()` function in `src/ingest.py` scans the input directory for `.jsonl` files, validates they're under 10 MB, then reads them line-by-line. For each line, it parses the JSON and attaches three pieces of provenance metadata: the source filename, the line number, and the Windows Event ID. If it encounters malformed JSON, it logs a warning and skips that line rather than crashing - this is graceful degradation. The function returns a list of Python dictionaries, each representing one event with provenance attached. This provenance is critical because when we later find suspicious activity, we can trace it back to the exact log file and line number for verification."

---

### **"Why not load everything into memory at once?"**

> "I have a 10 MB file size limit per file to prevent memory exhaustion. If someone accidentally tries to load a 2 GB log file, the system fails fast with a clear error message rather than crashing. For production use, you'd either increase this limit or implement streaming/chunked reading. The current limit is appropriate for demo datasets but shows I'm thinking about resource management and error handling."

---

### **"What happens if a log file is corrupted?"**

> "I have two levels of error handling. First, if the file can't be read at all - like permission denied or disk error - I log the error and skip that file but continue processing others. Second, if individual lines have malformed JSON - missing brackets, extra commas, etc. - I log a warning with the filename and line number, then skip just that line. This graceful degradation means one bad log entry doesn't kill the entire analysis. In production, you'd want monitoring to alert on high skip rates."

---

### **"Why use pathlib instead of os.path?"**

> "Pathlib is the modern, object-oriented way to work with file paths in Python. It's more readable and safer - methods like `.glob()`, `.read_text()`, and `.stat()` are cleaner than string concatenation with `os.path.join()`. It also handles cross-platform path differences automatically. While this project runs on Windows, using pathlib makes it more portable if we wanted Linux support later."

---

## **🔗 Connections to Other Phases**

**Where does ingest fit?**

```
Phase 0: prep_evtx.ps1 creates .jsonl files
    ↓
Phase 1: src/ingest.py loads events ← YOU ARE HERE
    ↓
Phase 2: src/llm_analyze.py analyzes events
    ↓
(Remaining phases...)
```

**What does Phase 2 receive?**
```python
events = load_events("data/evtx_parsed")
# events is now a List[dict] with 15 dictionaries
# Each has original event data + provenance metadata

analysis_data = analyze_events(events, model="gpt-4o-mini")
# Phase 2 receives the provenance-enriched events
```

---

## **📝 Quick Reference**

### **File:** [src/ingest.py](../src/ingest.py)

### **Main Function:** `load_events(input_dir: str) -> List[dict]`

### **Provenance Fields Added:**
- `source_file` - Filename (e.g., "Credential_hashdump.jsonl")
- `record_index` - Zero-based line number (0, 1, 2, ...)
- `event_id` - Windows Event ID as string (e.g., "4688")

### **Error Handling:**
- `FileNotFoundError` - No `.jsonl` files found
- `ValueError` - File exceeds 10 MB
- `json.JSONDecodeError` - Malformed JSON (logged, line skipped)

### **Constants:**
- `MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024` (10 MB)

---

## **🚀 Next Steps**

You now understand Phase 1! Move on to:
- **Lesson 04**: Phase 2 Deep Dive - LLM Analysis (how events are sent to OpenAI)
- **Lesson 07**: Hands-On Modification (add custom provenance fields)

You can now confidently explain how ingestion works and why provenance matters! 🎯
