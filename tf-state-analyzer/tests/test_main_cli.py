# tests/test_main_cli.py

import subprocess
import json
import tempfile
import os

def test_cli_runs_clean_state(tmp_path):
    clean_state = tmp_path / "clean.tfstate"
    clean_state.write_text(json.dumps({"resources": []}))

    result = subprocess.run(
        ["python", "src/main.py", "--state", str(clean_state)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Keine Secrets" in result.stdout

def test_cli_finds_secret(tmp_path):
    bad_state = tmp_path / "bad.tfstate"
    bad_state.write_text(json.dumps({
        "resources": [
            {"instances": [{"attributes": {"admin_password": "Secret123"}}]}
        ]
    }))

    result = subprocess.run(
        ["python", "src/main.py", "--state", str(bad_state)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 1
    assert "admin_password" in result.stdout