# tests/test_utils.py

from src.utils import walk_state

def test_walk_state_simple_dict():
    data = {"a": 1, "b": 2}
    results = list(walk_state(data))
    assert len(results) == 2
    assert results[0] == ("a", "a", 1)
    assert results[1] == ("b", "b", 2)

def test_walk_state_nested():
    data = {"a": {"b": {"c": 5}}}
    results = list(walk_state(data))
    assert results[0] == ("a.b.c", "c", 5)

def test_walk_state_list():
    data = [1, 2, 3]
    results = list(walk_state(data))
    assert results[0] == ("[0]", 0, 1)
    assert results[1] == ("[1]", 1, 2)
    assert results[2] == ("[2]", 2, 3)