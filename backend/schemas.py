from typing import Optional
from pydantic import BaseModel, Field, field_validator

class GateTelemetry(BaseModel):
    gate_id: str
    crowd_count: int = Field(ge=0, description="Current crowd count passing through or at the gate")
    status: str = Field(description="Gate status, e.g., OPEN, CLOSED, BOTTLENECK")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"OPEN", "CLOSED", "BOTTLENECK"}
        val = v.upper().strip()
        if val not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return val

class WeatherTelemetry(BaseModel):
    condition: str = Field(description="Weather condition description, e.g., CLEAR, RAIN, LIGHTNING")
    severity: str = Field(description="Severity classification: LOW, MEDIUM, HIGH")

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"LOW", "MEDIUM", "HIGH"}
        val = v.upper().strip()
        if val not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return val

class EmergencyTelemetry(BaseModel):
    threat_level: str = Field(description="Threat level: LOW, MEDIUM, HIGH, CRITICAL")
    location: str = Field(description="Specific location of the threat inside or outside the stadium")

    @field_validator('threat_level')
    @classmethod
    def validate_threat_level(cls, v: str) -> str:
        allowed = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        val = v.upper().strip()
        if val not in allowed:
            raise ValueError(f"threat_level must be one of {allowed}")
        return val

class TelemetryPayload(BaseModel):
    gate: Optional[GateTelemetry] = None
    weather: Optional[WeatherTelemetry] = None
    emergency: Optional[EmergencyTelemetry] = None
