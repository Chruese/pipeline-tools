# tests/test_secret_scanner.py

from src.secret_scanner import is_secret, scan_for_secrets

def test_is_secret_password():
    assert is_secret("admin_password", "SuperSecret123")

def test_is_secret_private_key():
    assert is_secret("private_key_pem", "-----BEGIN PRIVATE KEY-----")

def test_is_secret_false_positive_provider():
    assert not is_secret("provider", "registry.terraform.io/hashicorp/azurerm")

def test_scan_for_secrets():
    state = {
        "resources": [
            {
                "instances": [
                    {
                        "attributes": {
                            "admin_password": "Secret123"
                        }
                    }
                ]
            }
        ]
    }

    findings = scan_for_secrets(state)
    assert len(findings) == 1
    assert findings[0]["key"] == "admin_password"