#!/usr/bin/env python3
import sys
import json
import yaml
import re
import argparse
from typing import Dict, Any, List, Tuple


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Loads the naming convention rules from a YAML file."""
    with open(file_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    if "rules" not in config:
        raise ValueError("YAML config must contain a root key named 'rules'.")
    return config["rules"]


def load_terraform_plan(file_path: str) -> List[Dict[str, Any]]:
    """Loads and parses the Terraform plan JSON output."""
    with open(file_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
    return plan.get("resource_changes", [])


def validate_naming(
    resource_changes: List[Dict[str, Any]], 
    rules: Dict[str, Any]
) -> Tuple[List[str], List[str]]:
    """
    Validates the 'name' attribute of planned resources against regex patterns.
    Returns a tuple of (passed_resources, failed_resources).
    """
    passed = []
    failed = []

    for res in resource_changes:
        actions = res.get("change", {}).get("actions", [])
        
        # Skip deleted resources or resources without changes
        if actions == ["delete"] or actions == ["no-op"] or actions == ["read"]:
            continue

        res_type = res.get("type")
        
        # Skip resources that don't have a defined naming rule
        if res_type not in rules:
            continue

        # Extract the actual Azure resource name after Terraform interpolation
        after_data = res.get("change", {}).get("after", {})
        if not after_data or "name" not in after_data:
            continue

        actual_name = after_data.get("name")
        pattern = rules[res_type].get("pattern")
        example = rules[res_type].get("example", "No example provided")

        if not pattern:
            continue

        regex = re.compile(pattern)
        if regex.match(actual_name):
            passed.append(f"[✓] {res_type} : '{actual_name}'")
        else:
            failed.append(
                f"[!] {res_type} : '{actual_name}'\n"
                f"    -> Expected format: {pattern}\n"
                f"    -> Example: {example}"
            )

    return passed, failed


def main():
    parser = argparse.ArgumentParser(description="Validates Azure resource names in a TF plan against a YAML convention.")
    parser.add_argument("-p", "--plan", required=True, help="Path to the terraform plan JSON file")
    parser.add_argument("-c", "--config", required=True, help="Path to the naming-conventions.yaml file")

    args = parser.parse_args()

    try:
        rules = load_yaml_config(args.config)
    except Exception as e:
        print(f"[!] Error loading naming conventions: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        resource_changes = load_terraform_plan(args.plan)
    except Exception as e:
        print(f"[!] Error loading Terraform plan: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"[*] Checking naming conventions against {len(rules)} defined rules...\n")

    passed, failed = validate_naming(resource_changes, rules)

    for p in passed:
        print(p)

    if failed:
        print("\n" + "="*50)
        print("🚨 NAMING CONVENTION VIOLATIONS DETECTED 🚨")
        print("="*50)
        for f in failed:
            print(f)
            print("-" * 40)
        sys.exit(1)

    if passed:
        print(f"\n[✓] Successfully validated {len(passed)} resources.")
    else:
        print("\n[*] No resources matched the defined rules (nothing to validate).")
        
    sys.exit(0)


if __name__ == "__main__":
    main()