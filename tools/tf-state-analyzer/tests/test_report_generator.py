# tests/test_report_generator.py

from src.report_generator import (
    generate_text_report,
    generate_markdown_report,
    save_json_report
)
import os
import json

def test_text_report_no_findings():
    assert "Keine Secrets" in generate_text_report([])

def test_text_report_with_findings():
    findings = [{"path": "x", "key": "password", "type": "password", "value": "***"}]
    text = generate_text_report(findings)
    assert "password" in text

def test_markdown_report():
    findings = [{"path": "x", "key": "password", "type": "password", "value": "***"}]
    md = generate_markdown_report(findings)
    assert "| `password` |" in md

def test_json_report(tmp_path):
    findings = [{"key": "password"}]
    file_path = tmp_path / "report.json"

    assert save_json_report(findings, file_path)
    assert os.path.exists(file_path)

    with open(file_path) as f:
        data = json.load(f)
        assert data[0]["key"] == "password"