"""Zentrale Governance- und Security-Definitionen."""

# ROT: Grundsätzlich verboten (DORA / Security Baseline)
FORBIDDEN_PORTS = {
    21: "FTP (Unverschlüsselt)",
    23: "Telnet (Unverschlüsselt)",
    69: "TFTP",
    135: "RPC",
    445: "SMB (Lateral Movement Risiko)",
    3389: "RDP (Direktfreischaltung unzulässig)",
}

# GELB: Genehmigungspflichtig (Erfordert 'security_approval'-Block im YAML)
APPROVAL_REQUIRED_PORTS = {
    80: "HTTP (Unverschlüsselt - SecOps-Genehmigung erforderlich)",
    22: "SSH (Management-Port)",
    1433: "MS SQL Server",
    1521: "Oracle DB",
    3306: "MySQL",
    5432: "PostgreSQL",
}

MAX_EXPIRY_DAYS = 365