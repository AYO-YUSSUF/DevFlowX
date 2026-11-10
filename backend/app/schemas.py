from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ExperimentStatus = Literal["active", "completed", "archived"]
RunStatus = Literal["queued", "running", "succeeded", "failed"]


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    task: str = Field(min_length=1, max_length=160)
    dataset: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=1000)
    parameters: dict[str, Any] = Field(default_factory=dict)


class RunCreate(BaseModel):
    status: RunStatus = "succeeded"
    metrics: dict[str, float] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    model_name: str | None = Field(default=None, max_length=120)
    notes: str = Field(default="", max_length=1000)


class ModelVersion(BaseModel):
    id: str
    experiment_id: str
    run_id: str
    name: str
    version: int
    created_at: datetime
    metrics: dict[str, float]
    parent_model_id: str | None = None


class Run(BaseModel):
    id: str
    experiment_id: str
    status: RunStatus
    created_at: datetime
    parameters: dict[str, Any]
    metrics: dict[str, float]
    notes: str
    model_version: ModelVersion | None = None


class Experiment(BaseModel):
    id: str
    name: str
    task: str
    dataset: str
    description: str
    status: ExperimentStatus
    created_at: datetime
    updated_at: datetime
    parameters: dict[str, Any]
    runs: list[Run] = Field(default_factory=list)
    model_versions: list[ModelVersion] = Field(default_factory=list)


class GraphNode(BaseModel):
    id: str
    kind: Literal["experiment", "run", "model"]
    label: str
    detail: str = ""


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: Literal["HAS_RUN", "PRODUCED", "PARENT_OF"]


class WorkflowGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
