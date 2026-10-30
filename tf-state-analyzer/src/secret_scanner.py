# secret_scanner.py

import re
from utils import walk_state

# ---------------------------------------------------------
# 1. Ignore keys (never secrets)
# ---------------------------------------------------------

IGNORE_KEYS = {
    "provider",
    "type",
    "mode",
    "schema_version",
    "terraform_version",
    "version",
    "id",
    "name",
    "location",
    "tags",
    "resource_group_name",
}

# ---------------------------------------------------------
# 2. Secret keywords (precise, without false positives)
# ---------------------------------------------------------

SECRET_KEYWORDS = [
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "primary_access_key",
    "secondary_access_key",
    "connection_string",
    "private_key",
    "client_secret",
]

# ---------------------------------------------------------
# 3. Regex patterns for typical secrets
# ---------------------------------------------------------

SECRET_REGEX = [
    r"AKIA[0-9A-Z]{16}",                     # AWS Access Key
    r"AIza[0-9A-Za-z\-_]{35}",               # Google API Key
    r"ghp_[0-9A-Za-z]{36}",                  # GitHub Token
    r"-----BEGIN PRIVATE KEY-----",          # Private Key
    r"[A-Za-z0-9+/]{20,}={0,2}",             # Base64 Blob
]

# ---------------------------------------------------------
# 4. Azure connection string hints
# ---------------------------------------------------------

AZURE_KEY_HINTS = [
    "DefaultEndpointsProtocol=",
    "AccountKey=",
]


# ---------------------------------------------------------
# Secret detection
# ---------------------------------------------------------

def is_secret(key, value):
    """Checks if a key/value pair contains a secret."""

    # Key ignorieren?
    if key in IGNORE_KEYS:
        return False

    # Check key
    if key:
        key_lower = str(key).lower()
        for kw in SECRET_KEYWORDS:
            if kw in key_lower:
                return True

    # Value muss String sein
    if not isinstance(value, str):
        return False

    value_str = value.strip()

    # Azure Connection Strings
    for hint in AZURE_KEY_HINTS:
        if hint in value_str:
            return True

    # Check regex
    for pattern in SECRET_REGEX:
        if re.search(pattern, value_str):
            return True

    return False


# ---------------------------------------------------------
# Finding object
# ---------------------------------------------------------

def build_finding(path, key, value):
    return {
        "path": path,
        "key": key,
        "value": mask_value(value),
        "type": classify_secret(key, value),
    }


def classify_secret(key, value):
    key_lower = str(key).lower()

    if "private_key" in key_lower:
        return "private_key"
    if "password" in key_lower:
        return "password"
    if "connection" in key_lower:
        return "connection_string"
    if "token" in key_lower:
        return "token"
    if "access_key" in key_lower:
        return "access_key"

    return "secret"


def mask_value(value):
    """Masks secret values for reports."""
    if not isinstance(value, str):
        return value
    if len(value) <= 6:
        return "***"
    return value[:3] + "..." + value[-3:]


# ---------------------------------------------------------
# Main function
# ---------------------------------------------------------

def scan_for_secrets(state_dict):
    """Searches entire state file for secrets."""
    findings = []

    for path, key, value in walk_state(state_dict):
        if is_secret(key, value):
            findings.append(build_finding(path, key, value))

    return findings