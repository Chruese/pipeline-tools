# main.py

import argparse
import os
import sys

from state_loader import load_state
from secret_scanner import scan_for_secrets
from report_generator import save_report, generate_text_report


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Terraform State Analyzer – scans state files for secrets."
    )

    parser.add_argument(
        "--state",
        required=True,
        help="Path to Terraform state file (.tfstate)"
    )

    parser.add_argument(
        "--output",
        required=False,
        help="Optional: Path for report (.json, .md, .txt)"
    )

    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    state_path = args.state

    # -----------------------------------------
    # Check state file
    # -----------------------------------------
    if not os.path.exists(state_path):
        print(f"[ERROR] State file not found: {state_path}")
        sys.exit(2)

    # -----------------------------------------
    # Load state file
    # -----------------------------------------
    try:
        state = load_state(state_path)
    except Exception as e:
        print(f"[ERROR] Error loading state file: {e}")
        sys.exit(2)

    # -----------------------------------------
    # Perform secret scan
    # -----------------------------------------
    findings = scan_for_secrets(state)

    # -----------------------------------------
    # Output report
    # -----------------------------------------
    print(generate_text_report(findings))

    # -----------------------------------------
    # Optional: Save report
    # -----------------------------------------
    if args.output:
        if save_report(findings, args.output):
            print(f"\nReport saved to: {args.output}")

    # -----------------------------------------
    # Set exit code
    # -----------------------------------------
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()