# utils.py

def walk_state(data, path=""):
    """
    Recursively walks through any nested dict/list
    and returns a tuple for each key/value path:

        (complete_path, key, value)

    Examples of paths:
        resources[0].instances[0].attributes.admin_password
        resources[1].instances[0].attributes.private_key_pem

    Parameters:
        data: The current dict/list/value
        path: The path so far (string)

    Returns:
        Generator that yields (path, key, value)
    """

    # ---------------------------------------------------------
    # 1. Process dict
    # ---------------------------------------------------------
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key

            # If the value is a dict or list again → recurse further
            if isinstance(value, (dict, list)):
                yield from walk_state(value, new_path)
            else:
                # Primitive values → yield directly
                yield new_path, key, value

    # ---------------------------------------------------------
    # 2. Process list
    # ---------------------------------------------------------
    elif isinstance(data, list):
        for index, element in enumerate(data):
            new_path = f"{path}[{index}]"

            if isinstance(element, (dict, list)):
                yield from walk_state(element, new_path)
            else:
                # Primitive values in lists
                yield new_path, index, element

    # ---------------------------------------------------------
    # 3. Ignore primitive values
    # (werden nur in Dict/List verarbeitet)
    # ---------------------------------------------------------
    else:
        return