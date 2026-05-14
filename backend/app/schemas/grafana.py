from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class GrafanaAlert(BaseModel):
    status: Optional[str] = None
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    starts_at: str = Field(alias="startsAt")
    ends_at: Optional[str] = Field(default=None, alias="endsAt")
    fingerprint: Optional[str] = None
    generator_url: Optional[str] = Field(default=None, alias="generatorURL")
    silence_url: Optional[str] = Field(default=None, alias="silenceURL")
    dashboard_url: Optional[str] = Field(default=None, alias="dashboardURL")
    panel_url: Optional[str] = Field(default=None, alias="panelURL")
    values: dict[str, Any] = Field(default_factory=dict)
    value_string: Optional[str] = Field(default=None, alias="valueString")


class GrafanaWebhookPayload(BaseModel):
    receiver: Optional[str] = None
    status: Optional[str] = None
    org_id: Optional[int] = Field(default=None, alias="orgId")
    title: Optional[str] = None
    message: Optional[str] = None
    group_labels: dict[str, str] = Field(default_factory=dict, alias="groupLabels")
    common_labels: dict[str, str] = Field(default_factory=dict, alias="commonLabels")
    common_annotations: dict[str, str] = Field(default_factory=dict, alias="commonAnnotations")
    external_url: Optional[str] = Field(default=None, alias="externalURL")
    alerts: list[GrafanaAlert] = Field(default_factory=list)
