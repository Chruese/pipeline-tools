# state_loader.py

import json
import os

def load_state(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"State file not found: {path}")

    with open(path, "r") as f:
        state_dict = json.load(f)

    return state_dict