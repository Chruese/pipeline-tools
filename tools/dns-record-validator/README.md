# DNS Record Validator

A CLI tool for CI/CD pipelines that reads defined DNS records (`A`, `AAAA`, `CNAME`, `TXT`, `PTR`) from a YAML file and verifies them against internal or public nameservers.

Ideal for pre-flight checks before firewall or infrastructure deployments as well as post-deployment verification of private DNS zones.

## Features

- **Supported Record Types:** Checks `A`, `AAAA`, `CNAME`, `TXT`, `MX`, and reverse lookups (`PTR`).
- **Custom Nameserver:** Can specifically query internal core DNS servers, Azure Private DNS Resolvers, or public resolvers.
- **Fail-Fast:** Fails the pipeline with exit code `1` if a hostname is unresolvable (`NXDOMAIN`) or points to an incorrect IP.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## YAML Format (`dns-records.yaml`)

```yaml
records:
  - name: "api.intern.example.com"
    type: "A"
    expected: "10.20.1.15"

  - name: "portal.example.com"
    type: "CNAME"
    expected: "app-gateway.westeurope.cloudapp.azure.com"

  - name: "10.20.1.15"
    type: "PTR"
    expected: "api.intern.example.com"
```

## Usage

### Standard Resolution (System Resolver)

```bash
python dns_validator.py -f ./dns-records.yaml
```

### Query Against a Specific Internal DNS Server

```bash
python dns_validator.py -f ./dns-records.yaml --nameserver 10.100.0.4
```

### CLI Parameters

- `-f`, `--file`: Path to the YAML file containing DNS rules (Required)
- `-n`, `--nameserver`: IP address of a specific DNS server (Optional)
- `-t`, `--timeout`: Timeout in seconds per query (Default: `5.0`)

## Exit Codes

| Code | Description |
| :--- | :--- |
| `0` | All DNS records exist and match the expected values. |
| `1` | At least one DNS record deviates or could not be resolved. |
| `2` | Configuration or file error (invalid YAML). |

## Integration in GitHub Actions

```yaml
- name: Verify DNS Records
  run: |
    python tools/dns-record-validator/dns_validator.py \
      -f ./configs/expected-dns.yaml \
      --nameserver 10.0.0.4
```