from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

Action = Literal["update", "create", "reactivate", "deactivate", "manual"]

class FieldChange(BaseModel):
    field: str
    label: str
    old: Any | None = None
    new: Any | None = None
    section: str | None = None
    requires_manual: bool = False

class PropertyItem(BaseModel):
    id: str
    reference: str | None = None
    title: str
    action: Action
    source: str | None = None
    public_url: str | None = None
    approved: bool = False
    changes: list[FieldChange] = Field(default_factory=list)
    private_notes: str | None = None
    operator_notes: str | None = None

class ImobiPackage(BaseModel):
    package_version: str = "0.1"
    name: str
    created_at: str
    source_name: str | None = None
    operator: str = "Gustavo"
    dry_run_recommended: bool = True
    items: list[PropertyItem]
