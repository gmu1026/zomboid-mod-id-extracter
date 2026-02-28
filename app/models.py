from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class JobCreate(BaseModel):
    workshop_ids: List[str]


class ProgressEvent(BaseModel):
    workshop_id: str
    step: str
    message: str


class ModInfo(BaseModel):
    mod_id: str
    name: str
    mod_version: str
    requires: List[str]
    maps: List[str]


class WorkshopItem(BaseModel):
    workshop_id: str
    mods: List[ModInfo]
    server_config: Dict[str, str]


class JobResult(BaseModel):
    items: List[WorkshopItem]
    combined_config: Dict[str, str]


class JobResponse(BaseModel):
    id: str
    status: str
    workshop_ids: List[str]
    progress: List[ProgressEvent]
    result: Optional[JobResult] = None
    error: Optional[str] = None
    created_at: str
