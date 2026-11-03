from pydantic import BaseModel, ConfigDict, Field

from app.config import DEFAULT_TASK_PRIORITY, DEFAULT_TASK_STATUS


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = ""
    description: str = ""
    status: str = DEFAULT_TASK_STATUS
    priority: str = DEFAULT_TASK_PRIORITY


class TaskOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    created_at: str = Field(alias="createdAt")


class SummaryOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    owner: str
    total: int
    by_status: dict[str, int] = Field(alias="byStatus")
    high_priority_open: int = Field(alias="highPriorityOpen")


class UploadOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    owner: str
    file_name: str | None = Field(alias="fileName")
    stored_at: str = Field(alias="storedAt")
    size: int


class BackendHealthOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    requested_by: str = Field(alias="requestedBy")
    status: int
    body: str
