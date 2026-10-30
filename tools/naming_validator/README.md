# Naming Convention Validator

A lightweight Python CLI tool for CI/CD pipelines that enforces strict naming conventions on Azure infrastructure deployed via Terraform. 

Instead of statically analyzing raw `.tf` files (which fails when names are dynamically generated via variables and locals), this tool inspects the compiled **Terraform Plan JSON**. This ensures that the exact, fully-interpolated resource names destined for the Azure API are validated.

## Features

- **YAML-Driven:** Cloud architects can update naming conventions in a simple YAML file without modifying the pipeline code.
- **Regex Enforcement:** Uses regular expressions to strictly enforce prefixes, location codes, and numbering schemas.
- **Developer-Friendly:** On failure, it outputs the exact regex pattern and a valid example to help developers quickly fix their code.
- **Fail-Fast:** Returns exit code `1` if any violation is detected, preventing non-compliant infrastructure from being provisioned.

## YAML Configuration (`naming-conventions.yaml`)

Define your organization's naming rules by mapping Terraform resource types to regex patterns:

```yaml
rules:
  azurerm_resource_group:
    pattern: "^rg-[a-z0-9]+-(weu|gwc)-[0-9]{3}$"
    example: "rg-corenetwork-weu-001"
  
  azurerm_virtual_network:
    pattern: "^vnet-[a-z0-9]+-(weu|gwc)-[0-9]{3}$"
    example: "vnet-prod-weu-001"

  azurerm_storage_account:
    # Storage Accounts in Azure must be lowercase alphanumeric, 3-24 characters
    pattern: "^st[a-z0-9]{3,22}$"
    example: "stprodcorelogs001"
```

## Usage

1. **Generate the Terraform Plan as JSON:**
```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
```

2. **Run the Validator:**
```bash
python naming_validator.py --plan plan.json --config naming-conventions.yaml
```

### CLI Parameters

- `-p`, `--plan`: Path to the compiled `plan.json` file (Required)
- `-c`, `--config`: Path to the YAML ruleset file (Required)

## Exit Codes

| Code | Description |
| :--- | :--- |
| `0` | All evaluated resources strictly match the defined naming conventions. |
| `1` | One or more resources violate the naming conventions. |
| `2` | Technical error (missing files, invalid YAML, or unparseable JSON). |

## Integration in GitHub Actions

```yaml
- name: Terraform Plan
  run: |
    terraform plan -out=tfplan
    terraform show -json tfplan > plan.json

- name: Validate Azure Naming Conventions
  run: |
    python tools/naming-validator/naming_validator.py \
      --plan plan.json \
      --config configs/naming-conventions.yaml
```