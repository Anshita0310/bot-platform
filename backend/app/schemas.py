from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class Position(BaseModel):
    x: float
    y: float

class Node(BaseModel):
    id: str
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    position: Position

class Edge(BaseModel):
    id: str
    source: str
    target: str
    data: Dict[str, Any] = Field(default_factory=dict)

class FlowBase(BaseModel):
    orgId: str
    projectId: str
    name: str
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    version: int = 1
    isDraft: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FlowCreate(FlowBase):
    pass

class FlowUpdate(BaseModel):
    nodes: Optional[List[Node]] = None
    edges: Optional[List[Edge]] = None
    name: Optional[str] = None
    isDraft: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class FlowDB(FlowBase):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    id: Optional[str] = Field(default=None, alias="_id")
    createdAt: datetime
    updatedAt: datetime


# ── Auth ──

class UserSignup(BaseModel):
    email: str
    password: str
    name: str
    orgId: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserInfo(BaseModel):
    email: str
    name: str
    orgId: str

class UserOut(BaseModel):
    access_token: str
    user: UserInfo
