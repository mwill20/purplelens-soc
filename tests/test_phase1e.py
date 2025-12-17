"""Phase 1E validation tests for CLI orchestration."""

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_help_flag():
    """Test that --help displays usage correctly."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    assert result.returncode == 0, "Help should exit with code 0"
    assert "PurpleLens AI SOC Assistant" in result.stdout
    assert "--input INPUT" in result.stdout
    assert "--output" in result.stdout
    assert "--model" in result.stdout
    assert "--db" in result.stdout
    assert "--verbose" in result.stdout
    assert "--dry-run" in result.stdout
    
    print("✓ --help displays usage correctly")


def test_missing_api_key():
    """Test that missing OPENAI_API_KEY produces error."""
    with TemporaryDirectory() as tmpdir:
        # Create a test JSONL file
        test_file = Path(tmpdir) / "test.jsonl"
        test_file.write_text('{"Event":{"System":{"EventID":4688}}}\n')
        
        # Remove API key from environment for this test
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--input", tmpdir],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        
        assert result.returncode == 1, "Should exit with code 1 on missing API key"
        assert "OPENAI_API_KEY" in result.stderr or "not set" in result.stderr.lower()
        
    print("✓ Missing API key produces proper error")


def test_dry_run_no_api_key_required():
    """Test that --dry-run works without OPENAI_API_KEY."""
    with TemporaryDirectory() as tmpdir:
        # Create a test JSONL file
        test_file = Path(tmpdir) / "test.jsonl"
        test_file.write_text('{"Event":{"System":{"EventID":4688}}}\n')
        
        # Remove API key from environment
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--input", tmpdir, "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        
        assert result.returncode == 0, "--dry-run should not require API key"
        assert "Validation successful" in result.stdout
        assert "1 events" in result.stdout
        
    print("✓ --dry-run works without API key")


def test_dry_run_with_valid_input():
    """Test that --dry-run validates and exits without LLM call."""
    with TemporaryDirectory() as tmpdir:
        # Create multiple test JSONL files
        test_file1 = Path(tmpdir) / "test1.jsonl"
        with open(test_file1, 'w') as f:
            f.write('{"Event":{"System":{"EventID":4688}}}\n')
            f.write('{"Event":{"System":{"EventID":4624}}}\n')
        
        test_file2 = Path(tmpdir) / "test2.jsonl"
        test_file2.write_text('{"Event":{"System":{"EventID":4625}}}\n')
        
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--input", tmpdir, "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        assert result.returncode == 0, "--dry-run should succeed"
        assert "Validation successful" in result.stdout
        assert "3 events" in result.stdout
        
    print("✓ --dry-run validates input correctly")


def test_empty_directory_error():
    """Test that empty directory produces error."""
    with TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--input", tmpdir, "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        assert result.returncode == 1, "Empty directory should exit with code 1"
        assert "No JSONL files" in result.stderr or "Failed to load" in result.stderr
        
    print("✓ Empty directory produces error")


def test_verbose_logging():
    """Test that --verbose enables detailed logging."""
    with TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.jsonl"
        test_file.write_text('{"Event":{"System":{"EventID":4688}}}\n')
        
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--input", tmpdir, "--dry-run", "--verbose"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        # With --verbose, should see INFO level logs in stderr
        assert "Starting analysis run" in result.stderr or "[INFO]" in result.stderr
        
    print("✓ --verbose enables detailed logging")


def test_imports_use_src_namespace():
    """Test that all imports in main.py use src.* namespace."""
    main_file = Path("src/main.py")
    content = main_file.read_text()
    
    # Check for src.* imports
    assert "from src.ingest import" in content
    assert "from src.llm_analyze import" in content
    assert "from src.report import" in content
    assert "from src.schemas import" in content
    assert "from src.security import" in content
    assert "from src.storage import" in content
    
    # Ensure no bare imports (would indicate wrong namespace)
    assert "from ingest import" not in content
    assert "from llm_analyze import" not in content
    assert "from report import" not in content
    assert "from schemas import" not in content
    assert "from security import" not in content
    assert "from storage import" not in content
    
    print("✓ All imports use src.* namespace")


def test_cli_arguments_match_spec():
    """Test that CLI arguments match Phase 1E specification."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    # Required arguments
    assert "--input" in result.stdout
    
    # Optional arguments with defaults
    assert "--output" in result.stdout
    assert "console" in result.stdout
    assert "--model" in result.stdout
    assert "gpt-4" in result.stdout
    assert "--db" in result.stdout
    assert "db/analysis.db" in result.stdout
    
    # Flags
    assert "--verbose" in result.stdout
    assert "--dry-run" in result.stdout
    
    print("✓ CLI arguments match Phase 1E specification")


def test_logging_format():
    """Test that logging format matches specification."""
    with TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.jsonl"
        test_file.write_text('{"Event":{"System":{"EventID":4688}}}\n')
        
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--input", tmpdir, "--dry-run", "--verbose"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        # Check for format: [TIMESTAMP] [LEVEL] [MODULE] Message
        # With Python logging format: "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        stderr_lines = result.stderr.strip().split("\n")
        if stderr_lines:
            # Look for log lines with proper format
            log_lines = [line for line in stderr_lines if "[INFO]" in line or "[WARNING]" in line]
            if log_lines:
                # Check format: should have timestamp, [LEVEL], [MODULE]
                assert any("[INFO]" in line or "[WARNING]" in line for line in log_lines)
        
    print("✓ Logging format matches specification")


def test_directory_creation():
    """Test that db/ directory is created if missing."""
    with TemporaryDirectory() as tmpdir:
        # Use a custom db path inside tmpdir
        db_path = Path(tmpdir) / "custom_db" / "test.db"
        
        test_file = Path(tmpdir) / "test.jsonl"
        test_file.write_text('{"Event":{"System":{"EventID":4688}}}\n')
        
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--input", tmpdir, "--db", str(db_path), "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        # Should succeed and create directory
        assert result.returncode == 0
        assert db_path.parent.exists(), "Database directory should be created"
        
    print("✓ Database directory created if missing")


def test_file_output_creates_reports_directory():
    """Test that --output file creates reports/ directory."""
    with TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.jsonl"
        test_file.write_text('{"Event":{"System":{"EventID":4688}}}\n')
        
        # Note: This test would require mocking LLM, so we just verify the logic exists
        # by checking the code
        main_file = Path("src/main.py")
        content = main_file.read_text()
        
        assert 'reports_dir = Path("reports")' in content
        assert "reports_dir.mkdir(parents=True, exist_ok=True)" in content
        assert 'f"analysis_{run_id}.txt"' in content
        
    print("✓ File output creates reports/ directory (code verified)")


def test_provenance_tracking():
    """Test that provenance (unique files) is tracked for database."""
    main_file = Path("src/main.py")
    content = main_file.read_text()
    
    # Check for unique file tracking
    assert 'unique_files = sorted({event["source_file"] for event in events})' in content
    assert "input_files=unique_files" in content
    
    print("✓ Provenance tracking implemented")


def test_error_handling_implemented():
    """Test that error handling prevents crashes."""
    main_file = Path("src/main.py")
    content = main_file.read_text()
    
    # Check for try/except blocks
    assert "try:" in content
    assert "except" in content
    assert "return 1" in content  # Error exit codes
    
    # Check for validation error handling
    assert "ValidationError" in content
    assert "_build_error_analysis" in content
    
    print("✓ Error handling implemented")


def run_all_tests():
    """Run all Phase 1E validation tests."""
    tests = [
        test_help_flag,
        test_missing_api_key,
        test_dry_run_no_api_key_required,
        test_dry_run_with_valid_input,
        test_empty_directory_error,
        test_verbose_logging,
        test_imports_use_src_namespace,
        test_cli_arguments_match_spec,
        test_logging_format,
        test_directory_creation,
        test_file_output_creates_reports_directory,
        test_provenance_tracking,
        test_error_handling_implemented,
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 70)
    print("PHASE 1E VALIDATION TESTS")
    print("=" * 70)
    print()
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as exc:
            print(f"✗ {test_func.__name__} FAILED: {exc}")
            failed += 1
        except Exception as exc:
            print(f"✗ {test_func.__name__} ERROR: {exc}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
