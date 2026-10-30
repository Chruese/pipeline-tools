# report_generator.py

import json
import os


# ---------------------------------------------------------
# JSON Report
# ---------------------------------------------------------

def save_json_report(findings, output_path):
    """
    Saves the findings as a JSON file.
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=4)
        return True
    except Exception as e:
        print(f"[ERROR] Could not save JSON report: {e}")
        return False


# ---------------------------------------------------------
# Text Report (CLI)
# ---------------------------------------------------------

def generate_text_report(findings):
    """
    Generates a formatted text report for CLI output.
    """
    if not findings:
        return "✔ No secrets found."

    lines = ["⚠ Secrets found:"]
    for f in findings:
        lines.append(
            f"- {f['path']} | {f['key']} | {f['type']} | {f['value']}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------
# Markdown Report (for pull requests)
# ---------------------------------------------------------

def generate_markdown_report(findings):
    """
    Generates a markdown report, ideal for pull requests.
    """
    if not findings:
        return "### ✔ No secrets found"

    md = ["### ⚠ Secrets found", ""]
    md.append("| Path | Key | Type | Value |")
    md.append("|------|-----|-----|------|")

    for f in findings:
        md.append(
            f"| `{f['path']}` | `{f['key']}` | `{f['type']}` | `{f['value']}` |"
        )

    return "\n".join(md)


# ---------------------------------------------------------
# Helper: Auto-save by format
# ---------------------------------------------------------

def save_report(findings, output_path):
    """
    Saves the report based on file extension:
    - .json → JSON
    - .md   → Markdown
    - .txt  → Text
    """
    ext = os.path.splitext(output_path)[1].lower()

    if ext == ".json":
        return save_json_report(findings, output_path)

    elif ext == ".md":
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(generate_markdown_report(findings))
            return True
        except Exception as e:
            print(f"[ERROR] Konnte Markdown-Report nicht speichern: {e}")
            return False

    elif ext == ".txt":
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(generate_text_report(findings))
            return True
        except Exception as e:
            print(f"[ERROR] Konnte Text-Report nicht speichern: {e}")
            return False

    else:
        print(f"[ERROR] Unbekanntes Report-Format: {ext}")
        return False