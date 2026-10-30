# tests/test_state_loader.py

import json
import pytest
from src.state_loader import load_state

def test_load_state_valid(tmp_path):
    file_path = tmp_path / "state.tfstate"
    file_path.write_text(json.dumps({"test": 123}))

    state = load_state(file_path)
    assert state["test"] == 123

def test_load_state_missing():
    with pytest.raises(FileNotFoundError):
        load_state("does_not_exist.tfstate")