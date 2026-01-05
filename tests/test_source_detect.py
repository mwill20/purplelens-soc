"""
Usage:
  pytest tests/test_source_detect.py

Purpose:
  Validate source detection logic for Windows, AWS, and GCP inputs.

Limitations:
  - Uses temporary files; does not validate full dataset content.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.main import detect_source


class TestSourceDetection:
    def test_evtx_file_detected(self):
        """Test .evtx file detection"""
        with tempfile.NamedTemporaryFile(suffix=".evtx") as tmp:
            source, reason = detect_source(Path(tmp.name))
            assert source == "windows"
            assert "EVTX extension" in reason

    def test_cloudtrail_json_detected(self):
        """Test CloudTrail JSON detection"""
        cloudtrail_data = {"Records": [{"eventVersion": "1.05"}]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(cloudtrail_data, tmp)
            tmp.flush()

        try:
            source, reason = detect_source(Path(tmp.name))
            assert source == "aws"
            assert "CloudTrail schema" in reason
        finally:
            import os

            os.unlink(tmp.name)

    def test_generic_json_fallback(self):
        """Test generic JSON falls back to windows"""
        generic_data = {"some": "data"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as tmp:
            json.dump(generic_data, tmp)
            tmp.flush()
            source, reason = detect_source(Path(tmp.name))
            assert source == "windows"

    def test_mixed_directory_fails(self):
        """Test mixed directory raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Create both file types
            (tmpdir / "test.evtx").touch()
            (tmpdir / "test.json").touch()

            with pytest.raises(SystemExit) as exc:
                detect_source(tmpdir)
            assert "Ambiguous input" in str(exc.value)
            assert "--source" in str(exc.value)

    def test_evtx_directory(self):
        """Test directory with only EVTX files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "test1.evtx").touch()
            (tmpdir / "test2.evtx").touch()

            source, reason = detect_source(tmpdir)
            assert source == "windows"
            assert "2 EVTX files" in reason
