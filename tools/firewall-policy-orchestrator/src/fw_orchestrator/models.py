import ipaddress
from datetime import date, timedelta
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from .config import FORBIDDEN_PORTS, APPROVAL_REQUIRED_PORTS, MAX_EXPIRY_DAYS

class SecurityApproval(BaseModel):
    secops_ticket: str = Field(..., pattern=r"^SEC-\d{4}-\d+$")
    approved_by: str = Field(..., min_length=5)
    justification: str = Field(..., min_length=15, max_length=300)

class ServiceItem(BaseModel):
    protocol: Literal["tcp", "udp", "icmp"]
    ports: List[str] = Field(..., min_length=1)

    @field_validator("ports")
    @classmethod
    def validate_ports(cls, ports: List[str]) -> List[str]:
        for p in ports:
            if p == "*":
                raise ValueError("Wildcard-Ports ('*') sind verboten!")
            nums = range(int(p.split("-")[0]), int(p.split("-")[1]) + 1) if "-" in p else [int(p)]
            for num in nums:
                if num in FORBIDDEN_PORTS:
                    raise ValueError(f"Port {num} ist unzulässig: {FORBIDDEN_PORTS[num]}")
        return ports

class EndpointSpec(BaseModel):
    app_short_name: str = Field(..., pattern=r"^[a-z0-9]{2,12}$")
    unit: str = Field(..., min_length=3)
    cidrs: List[str] = Field(..., min_length=1)

    @field_validator("cidrs")
    @classmethod
    def validate_cidrs(cls, cidrs: List[str]) -> List[str]:
        for c in cidrs:
            if ipaddress.ip_network(c, strict=False).prefixlen == 0:
                raise ValueError(f"Any-Regeln ({c}) sind unzulässig!")
        return cidrs

class RuleSpec(BaseModel):
    rule_id: str = Field(..., pattern=r"^\d{2,3}$")
    description: str = Field(..., min_length=10, max_length=200)
    action: Literal["allow", "deny"]
    direction: Literal["ingress", "egress"]
    owning_unit: str
    source: EndpointSpec
    destination: EndpointSpec
    services: List[ServiceItem] = Field(..., min_length=1)
    security_approval: Optional[SecurityApproval] = None

    def requires_approval(self) -> bool:
        for svc in self.services:
            for p in svc.ports:
                nums = range(int(p.split("-")[0]), int(p.split("-")[1]) + 1) if "-" in p else [int(p)]
                if any(n in APPROVAL_REQUIRED_PORTS for n in nums):
                    return True
        return False

    @model_validator(mode="after")
    def check_approval(self) -> "RuleSpec":
        if self.requires_approval() and self.security_approval is None:
            raise ValueError(
                "Genehmigungspflichtiger Port (z.B. HTTP/80) erkannt, aber 'security_approval' fehlt!"
            )
        return self

class TicketPolicy(BaseModel):
    schema_version: Literal["1.0"]
    change_id: str = Field(..., pattern=r"^CHG-\d{4}-\d+$")
    environment: Literal["dev", "stage", "prod"]
    requested_by: str
    expiry_date: date
    target_platforms: List[Literal["azure", "checkpoint", "aws"]] = Field(..., min_length=1)
    rules: List[RuleSpec] = Field(..., min_length=1)

    @field_validator("expiry_date")
    @classmethod
    def check_expiry(cls, exp: date) -> date:
        today = date.today()
        if exp <= today or exp > today + timedelta(days=MAX_EXPIRY_DAYS):
            raise ValueError(f"expiry_date ({exp}) muss in Zukunft liegen (max. {MAX_EXPIRY_DAYS} Tage).")
        return exp