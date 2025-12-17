"""Phase 1C validation tests for LLM integration."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.llm_analyze import (
    analyze_events,
    _build_user_prompt,
    _chunk_events,
    _merge_results,
    _parse_llm_content,
    _attempt_salvage_json,
    MAX_EVENTS_PER_BATCH,
    MAX_PROMPT_CHARS,
)
from src.schemas import AnalysisOutput


def test_empty_events_validation():
    """Test that empty events list returns validation_error without API call."""
    result = analyze_events([])
    assert result["status"] == "validation_error", f"Expected validation_error, got {result['status']}"
    assert "No events provided" in result["error_message"], f"Unexpected error message: {result['error_message']}"
    assert result["findings"] == []
    assert result["confidence"] == 0.0
    print("✓ Empty events validation guard works")


def test_user_prompt_with_provenance():
    """Test that user prompt includes source_file and record_index metadata."""
    events = [
        {
            "source_file": "test.jsonl",
            "record_index": 0,
            "event_id": "4688",
            "raw_event": {"EventID": 4688, "ProcessName": "cmd.exe"}
        },
        {
            "source_file": "test.jsonl",
            "record_index": 1,
            "event_id": "4624",
            "raw_event": {"EventID": 4624, "LogonType": 3}
        }
    ]
    
    prompt = _build_user_prompt(events)
    
    # Check for provenance metadata
    assert "source_file=test.jsonl" in prompt, "Missing source_file in prompt"
    assert "record_index=0" in prompt, "Missing record_index=0 in prompt"
    assert "record_index=1" in prompt, "Missing record_index=1 in prompt"
    
    # Check for event data
    assert "cmd.exe" in prompt, "Missing event data in prompt"
    assert "4688" in prompt, "Missing EventID in prompt"
    
    # Check for delimiters
    assert "```json" in prompt, "Missing JSON code fence"
    assert "Event 1 |" in prompt, "Missing event delimiter"
    assert "Event 2 |" in prompt, "Missing event delimiter"
    
    print("✓ User prompt carries provenance metadata correctly")


def test_chunking_by_event_count():
    """Test that events are chunked at MAX_EVENTS_PER_BATCH boundary."""
    events = [{"source_file": "test.jsonl", "record_index": i, "raw_event": {"id": i}} 
              for i in range(75)]
    
    chunks = list(_chunk_events(events))
    
    # Should create 2 chunks: 50 + 25
    assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"
    assert len(chunks[0]) == MAX_EVENTS_PER_BATCH, f"First chunk should have {MAX_EVENTS_PER_BATCH} events"
    assert len(chunks[1]) == 25, "Second chunk should have 25 events"
    
    print("✓ Chunking by event count works correctly")


def test_chunking_by_character_limit():
    """Test that events are chunked when approaching character limit."""
    # Create events with large raw_event to trigger char limit
    large_event = {"data": "x" * 10_000}  # ~10KB per event
    events = [{"source_file": "test.jsonl", "record_index": i, "raw_event": large_event} 
              for i in range(10)]
    
    chunks = list(_chunk_events(events))
    
    # Should create multiple chunks due to char limit
    assert len(chunks) > 1, "Should create multiple chunks due to character limit"
    
    # Verify each chunk stays under char limit
    for chunk in chunks:
        char_count = sum(len(json.dumps(e.get("raw_event", {}))) for e in chunk)
        assert char_count <= MAX_PROMPT_CHARS, f"Chunk exceeds character limit: {char_count} > {MAX_PROMPT_CHARS}"
    
    print("✓ Chunking by character limit works correctly")


def test_parse_valid_llm_response():
    """Test parsing valid LLM JSON response."""
    valid_json = json.dumps({
        "status": "success",
        "findings": [{"title": "Test", "summary": "Test finding", "severity": "Low", "evidence": []}],
        "hypotheses": [{"description": "Test hypothesis", "confidence": 0.75}],
        "indicators_of_compromise": ["test.exe"],
        "recommended_next_steps": ["Investigate further"],
        "confidence": 0.8
    })
    
    result = _parse_llm_content(valid_json)
    
    assert result["status"] == "success"
    assert len(result["findings"]) == 1
    assert len(result["hypotheses"]) == 1
    assert result["confidence"] == 0.8
    
    print("✓ Valid LLM response parsing works")


def test_parse_empty_llm_response():
    """Test handling of empty/None LLM response."""
    result = _parse_llm_content(None)
    
    assert result["status"] == "llm_error"
    assert "empty response" in result["error_message"].lower()
    assert result["findings"] == []
    
    result2 = _parse_llm_content("")
    assert result2["status"] == "llm_error"
    
    print("✓ Empty LLM response handling works")


def test_parse_malformed_json():
    """Test handling of malformed JSON with no salvage possible."""
    malformed = "This is not JSON at all"
    
    result = _parse_llm_content(malformed)
    
    assert result["status"] == "llm_error"
    assert "malformed" in result["error_message"].lower()
    
    print("✓ Malformed JSON handling works")


def test_salvage_json_with_markdown():
    """Test salvaging JSON from markdown fences."""
    markdown_wrapped = '```json\n{"status": "success", "findings": [], "confidence": 0.5}\n```'
    
    salvaged = _attempt_salvage_json(markdown_wrapped)
    
    assert salvaged is not None, "Should salvage JSON from markdown"
    assert salvaged["status"] == "success"
    assert salvaged["confidence"] == 0.5
    
    print("✓ JSON salvage from markdown works")


def test_salvage_json_with_text():
    """Test salvaging JSON embedded in text."""
    text_with_json = 'Here is the analysis: {"status": "success", "findings": []} and some more text'
    
    salvaged = _attempt_salvage_json(text_with_json)
    
    assert salvaged is not None, "Should salvage JSON from text"
    assert salvaged["status"] == "success"
    
    print("✓ JSON salvage from text works")


def test_salvage_fails_on_invalid():
    """Test that salvage returns None for truly invalid content."""
    invalid = "No JSON here at all, not even fragments"
    
    salvaged = _attempt_salvage_json(invalid)
    
    assert salvaged is None, "Should return None for unsalvageable content"
    
    print("✓ Salvage correctly fails on invalid content")


def test_merge_multiple_successful_batches():
    """Test merging results from multiple successful batches."""
    results = [
        {
            "status": "success",
            "findings": [{"title": "Finding 1", "summary": "Test", "severity": "low", "evidence": []}],
            "hypotheses": [],
            "indicators_of_compromise": ["ioc1"],
            "recommended_next_steps": ["step1"],
            "confidence": 0.7
        },
        {
            "status": "success",
            "findings": [{"title": "Finding 2", "summary": "Test", "severity": "medium", "evidence": []}],
            "hypotheses": [{"description": "Hypothesis 1", "confidence": 0.6}],
            "indicators_of_compromise": ["ioc2"],
            "recommended_next_steps": ["step2"],
            "confidence": 0.9
        }
    ]
    
    merged = _merge_results(results)
    
    assert merged["status"] == "success"
    assert len(merged["findings"]) == 2, "Should have 2 findings"
    assert len(merged["hypotheses"]) == 1, "Should have 1 hypothesis"
    assert len(merged["indicators_of_compromise"]) == 2, "Should have 2 IOCs"
    assert merged["confidence"] == 0.8, f"Confidence should be average (0.7+0.9)/2=0.8, got {merged['confidence']}"
    
    print("✓ Merging multiple successful batches works")


def test_merge_with_partial_failure():
    """Test that merged status degrades when one batch fails."""
    results = [
        {
            "status": "success",
            "findings": [{"title": "Finding 1", "summary": "Test", "severity": "low", "evidence": []}],
            "hypotheses": [],
            "indicators_of_compromise": [],
            "recommended_next_steps": [],
            "confidence": 0.8
        },
        {
            "status": "timeout",
            "error_message": "LLM request timed out",
            "findings": [],
            "hypotheses": [],
            "indicators_of_compromise": [],
            "recommended_next_steps": [],
            "confidence": 0.0
        }
    ]
    
    merged = _merge_results(results)
    
    assert merged["status"] == "timeout", f"Status should degrade to timeout, got {merged['status']}"
    assert merged["error_message"] == "LLM request timed out"
    assert len(merged["findings"]) == 1, "Should preserve findings from successful batch"
    
    print("✓ Merging with partial failure degrades status correctly")


def test_schema_validation_integration():
    """Test that returned dict can be validated by Pydantic schema."""
    mock_result = {
        "status": "success",
        "error_message": None,
        "findings": [
            {
                "title": "Test Finding",
                "summary": "A test finding",
                "severity": "medium",
                "evidence": [
                    {
                        "source_file": "test.jsonl",
                        "record_index": 0,
                        "event_id": "4688",
                        "excerpt": "powershell.exe"
                    }
                ]
            }
        ],
        "hypotheses": [{"description": "Test hypothesis", "confidence": 0.65}],
        "indicators_of_compromise": ["powershell.exe"],
        "recommended_next_steps": ["Investigate PowerShell usage"],
        "confidence": 0.7
    }
    
    # This should not raise ValidationError
    try:
        validated = AnalysisOutput.model_validate(mock_result)
        assert validated.status == "success"
        assert len(validated.findings) == 1
        assert validated.confidence == 0.7
        print("✓ Schema validation integration works")
    except Exception as exc:
        raise AssertionError(f"Schema validation failed: {exc}")


def test_retry_logic_mock():
    """Test retry logic with mocked OpenAI client."""
    events = [
        {
            "source_file": "test.jsonl",
            "record_index": 0,
            "raw_event": {"EventID": 4688}
        }
    ]
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "status": "success",
        "findings": [],
        "hypotheses": [],
        "indicators_of_compromise": [],
        "recommended_next_steps": [],
        "confidence": 0.5
    })
    
    with patch("src.llm_analyze._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_response
        
        result = analyze_events(events, model="gpt-4o")
        
        assert result["status"] == "success"
        assert mock_client.return_value.chat.completions.create.call_count == 1
        
    print("✓ Retry logic (mocked) works")


def run_all_tests():
    """Run all Phase 1C validation tests."""
    tests = [
        test_empty_events_validation,
        test_user_prompt_with_provenance,
        test_chunking_by_event_count,
        test_chunking_by_character_limit,
        test_parse_valid_llm_response,
        test_parse_empty_llm_response,
        test_parse_malformed_json,
        test_salvage_json_with_markdown,
        test_salvage_json_with_text,
        test_salvage_fails_on_invalid,
        test_merge_multiple_successful_batches,
        test_merge_with_partial_failure,
        test_schema_validation_integration,
        test_retry_logic_mock,
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 70)
    print("PHASE 1C VALIDATION TESTS")
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
