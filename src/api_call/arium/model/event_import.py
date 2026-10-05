from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from dataclasses_json import dataclass_json, DataClassJsonMixin, Undefined


class ImportFormat(Enum):
    CSV = "csv"
    SCE = "sce"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RejectedEvent(DataClassJsonMixin):
    event: Optional[str] = None
    errors: List[str] = field(default_factory=list)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class EventImportResponse(DataClassJsonMixin):
    """Response of a queued bulk event import or export. Follow it with ActivityClient.get/wait(activityId)."""
    activityId: str
    total: Optional[int] = None
    warnings: List[str] = field(default_factory=list)
    rejected: List[RejectedEvent] = field(default_factory=list)
