from typing import Any

from pydantic import BaseModel, Field


class AttackRequest(BaseModel):
    attack_type: str = Field(..., examples=["sql_injection"])
    target: str = Field(..., examples=["vuln-node-api"])
    params: dict[str, Any] = Field(default_factory=dict)


class CampaignRequest(BaseModel):
    scenario_id: str = Field(..., examples=["web_app_pentest"])


class LogEvent(BaseModel):
    correlation_id: str
    attack_type: str
    level: str = "info"          # info|success|warn|error
    message: str
    progress: int = 0            # 0..100
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class AttackModuleInfo(BaseModel):
    id: str
    name: str
    description: str
    default_target: str
    mitre: str
    params_schema: dict[str, Any] = Field(default_factory=dict)
