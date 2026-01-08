# 🔗 **Lesson 02: Understanding The Harness - How Files Connect**

This lesson explains the **"harness"** (also called the orchestrator) and demystifies how Python files talk to each other through imports.

---

## **🧠 What is the "Harness"?**

**In plain English:** The harness is the **backbone/spine** of your project that:
1. Imports functions from all other files
2. Calls them in the right order
3. Connects everything together into one working system

**In this project:** The harness = [src/main.py](../src/main.py)

Think of it like a **conductor leading an orchestra**:
- The violins (ingest.py), trumpets (llm_analyze.py), and drums (storage.py) each know their parts
- The conductor (main.py) brings them all together at the right time
- Without the conductor, you just have individual musicians

---

## **📖 How Python Files Talk to Each Other: Imports**

### **The Pattern You Need to Know**

```python
from [folderName].[fileName] import [functionName]
```

**Real example from your project:**
```python
from src.ingest import load_events
```

**Translation:**
- `from src.ingest` = "Go to folder `src`, find file `ingest.py`"
- `import load_events` = "Grab the function called `load_events`"
- Now I can use `load_events()` in this file

---

## **🔍 Let's Look at Real Imports from Your Project**

Open [src/main.py](../src/main.py) and look at **lines 23-29**:

```python
from src.ingest import load_events
from src.llm_analyze import analyze_events
from src.report import generate_report
from src.schemas import AnalysisOutput
from src.security import validate_output
from src.storage import initialize_database, save_analysis
```

### **Breaking Down Each Import**

#### **Import #1: Ingest**
```python
from src.ingest import load_events
```
- **File**: [src/ingest.py](../src/ingest.py)
- **What it grabs**: The `load_events()` function
- **What that function does**: Reads `.jsonl` files and returns a list of events
- **Where it's called**: Line 103 in `main.py`: `events = load_events(args.input)`

---

#### **Import #2: LLM Analysis**
```python
from src.llm_analyze import analyze_events
```
- **File**: [src/llm_analyze.py](../src/llm_analyze.py)
- **What it grabs**: The `analyze_events()` function
- **What that function does**: Sends events to OpenAI and gets back analysis
- **Where it's called**: Line 114 in `main.py`: `analysis_data = analyze_events(events, model=args.model)`

---

#### **Import #3: Report Generator**
```python
from src.report import generate_report
```
- **File**: [src/report.py](../src/report.py)
- **What it grabs**: The `generate_report()` function
- **What that function does**: Formats findings into markdown report
- **Where it's called**: Line 127 in `main.py`: `report_text = generate_report(analysis)`

---

#### **Import #4: Data Models**
```python
from src.schemas import AnalysisOutput
```
- **File**: [src/schemas.py](../src/schemas.py)
- **What it grabs**: The `AnalysisOutput` class (a Pydantic model/template)
- **What it does**: Defines what valid analysis data looks like
- **Where it's used**: Line 115 in `main.py`: `analysis = _validate_analysis_output(analysis_data)`

---

#### **Import #5: Security Validation**
```python
from src.security import validate_output
```
- **File**: [src/security.py](../src/security.py)
- **What it grabs**: The `validate_output()` function
- **What that function does**: Checks for prohibited patterns in the AI's response
- **Where it's called**: Lines 117-119 in `main.py`

---

#### **Import #6: Database Storage (Multiple Functions)**
```python
from src.storage import initialize_database, save_analysis
```
- **File**: [src/storage.py](../src/storage.py)
- **What it grabs**: TWO functions separated by comma
  - `initialize_database()` - Creates the SQLite tables
  - `save_analysis()` - Saves the results
- **Where they're called**:
  - `initialize_database(args.db)` at line 113
  - `save_analysis(...)` at line 130

**Note:** You can import multiple things from one file by separating them with commas!

---

## **🔧 The Harness in Action: The `main()` Function**

Now let's see how the harness **orchestrates** all these imported functions.

Open [src/main.py](../src/main.py) and find the `main()` function (starts at line 86):

```python
def main() -> int:
    """The orchestrator - connects all phases."""
    
    # Step 1: Setup (parse CLI arguments, generate run ID)
    args = parse_args()
    configure_logging(args.verbose)
    run_id = str(uuid.uuid4())
    
    # Step 2: Validate environment (API key, directories)
    if not ensure_environment(args):
        return 1
    
    # Step 3: PHASE 1 - INGEST
    # Calls the imported load_events() function
    try:
        events = load_events(args.input)  # ← From src/ingest.py
    except Exception as exc:
        LOGGER.error("Failed to load events: %s", exc)
        return 1
    
    # Step 4: Dry run early exit (if user just wants validation)
    if args.dry_run:
        print(f"Validation successful. Loaded {len(events)} events from {args.input}.")
        return 0
    
    # Step 5: Initialize database
    initialize_database(args.db)  # ← From src/storage.py
    
    # Step 6: PHASE 2 - ANALYZE
    # Calls the imported analyze_events() function
    analysis_data = analyze_events(events, model=args.model)  # ← From src/llm_analyze.py
    
    # Step 7: PHASE 3 - VALIDATE
    # Schema validation (using imported AnalysisOutput class)
    analysis = _validate_analysis_output(analysis_data)  # ← Uses src/schemas.py
    
    # Security validation (using imported validate_output function)
    policy_valid, policy_error = validate_output(
        json.dumps(analysis_data, ensure_ascii=False)
    )  # ← From src/security.py
    
    if not policy_valid:
        LOGGER.error("Security policy violation: %s", policy_error)
        analysis = _build_error_analysis("validation_error", policy_error)
    
    # Step 8: PHASE 4 - REPORT
    # Calls the imported generate_report() function
    report_text = generate_report(analysis)  # ← From src/report.py
    
    # Output the report (console or file)
    _output_report(report_text, args.output, run_id)
    
    # Step 9: PHASE 5 - PERSIST
    # Calls the imported save_analysis() function
    try:
        save_analysis(
            db_path=args.db,
            run_id=run_id,
            analysis=analysis,
            input_files=unique_files,
            model_used=args.model,
            report_text=report_text,
            report_generated_at=datetime.now(timezone.utc),
            run_timestamp=run_timestamp,
        )  # ← From src/storage.py
    except Exception as exc:
        LOGGER.error("Failed to persist analysis: %s", exc)
        return 1
    
    # Step 10: Done!
    LOGGER.info("Analysis complete with status=%s", analysis.status)
    return 0 if analysis.status == "success" else 1
```

---

## **📊 Visual: How the Harness Connects Everything**

```
┌──────────────────────────────────────────────────────────┐
│                     src/main.py                          │
│                   (THE HARNESS)                          │
│                                                          │
│  Imports:                                                │
│  ┌────────────────────────────────────────────────────┐ │
│  │ from src.ingest import load_events                 │ │
│  │ from src.llm_analyze import analyze_events         │ │
│  │ from src.report import generate_report             │ │
│  │ from src.schemas import AnalysisOutput             │ │
│  │ from src.security import validate_output           │ │
│  │ from src.storage import initialize_database, ...   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  main() function orchestrates:                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  events = load_events(...)          ← ingest.py   │ │
│  │  analysis = analyze_events(...)      ← llm_analyze│ │
│  │  validate_output(...)                ← security   │ │
│  │  report = generate_report(...)       ← report     │ │
│  │  save_analysis(...)                  ← storage    │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
           ↓         ↓         ↓         ↓         ↓
     ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
     │ingest.py│ │llm_     │ │security │ │report.py│ │storage  │
     │         │ │analyze  │ │.py      │ │         │ │.py      │
     └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## **🎯 Key Takeaways**

### **1. The Harness (main.py) Has Three Jobs:**
- ✅ **Import** functions from other files
- ✅ **Orchestrate** them in the right order
- ✅ **Handle** errors and return codes

### **2. Import Syntax:**
```python
from [package].[module] import [function_or_class]
```
- Package = folder name (e.g., `src`)
- Module = file name without `.py` (e.g., `ingest`)
- Function/Class = what you want to use (e.g., `load_events`)

### **3. Multiple Imports from One File:**
```python
from src.storage import initialize_database, save_analysis
```
Separate multiple items with commas.

### **4. Why This Matters:**
- **Modularity**: Each file does one thing well
- **Testability**: You can test `ingest.py` independently
- **Maintainability**: Change one file without breaking others
- **Readability**: The harness shows the whole workflow at a glance

---

## **🔍 Exercise: Trace an Import**

Let's practice! Pick one import and trace it:

### **Example: Tracing `load_events`**

1. **Find the import in main.py (line 23):**
   ```python
   from src.ingest import load_events
   ```

2. **Ctrl+Click on `load_events`** → Jumps to [src/ingest.py](../src/ingest.py)

3. **Find the function definition:**
   ```python
   def load_events(input_dir: str) -> List[dict]:
       """Load all JSONL files from directory."""
       # ... implementation ...
   ```

4. **See where it's called in main.py (line 103):**
   ```python
   events = load_events(args.input)
   ```

5. **Understand the flow:**
   - User runs: `python -m src.main --input data/evtx_parsed`
   - `main()` function parses args
   - Calls `load_events("data/evtx_parsed")`
   - `load_events()` reads the directory and returns events
   - `events` variable now holds the data

---

## **❓ Common Questions**

### **Q: Why not put everything in one big file?**
A: Separation of concerns. Each file has one job:
- `ingest.py` = file I/O
- `llm_analyze.py` = API calls
- `security.py` = policy enforcement
- `report.py` = formatting
- `storage.py` = database operations

This makes testing, debugging, and modification easier.

---

### **Q: What's the difference between `import` and `from...import`?**

**Method 1: `import`**
```python
import src.ingest
# Now you call: src.ingest.load_events()
```

**Method 2: `from...import`** (what we use)
```python
from src.ingest import load_events
# Now you call: load_events()
```

Method 2 is cleaner and more readable.

---

### **Q: Can I import from files in subdirectories?**
Yes! That's what we do:
```python
from src.ingest import load_events
#    ↑    ↑       ↑
#    folder  file   function
```

---

### **Q: What if I import something that doesn't exist?**
Python will throw an `ImportError` or `ModuleNotFoundError`:
```python
from src.nonexistent import fake_function
# Error: ModuleNotFoundError: No module named 'src.nonexistent'
```

---

## **🎯 Interview Talking Points**

When asked "How does your project structure work?":

> "I use a modular architecture where each file has one responsibility. The harness - that's `main.py` - imports functions from all the specialized modules and orchestrates them in a 5-phase pipeline. For example, `from src.ingest import load_events` lets me use the file loading logic without duplicating code. This separation makes the system testable - I can mock the LLM layer and test everything else independently. It also makes it maintainable - if I want to swap OpenAI for a different provider, I only change one file."

---

## **🚀 Next Steps**

Now that you understand the harness and imports:
1. Open [src/main.py](../src/main.py) and read through `main()` function
2. For each function call, Ctrl+Click to see where it comes from
3. Move on to **Lesson 03** to deep dive into Phase 1 (Ingest)

You now understand how the whole system connects! 🎯
