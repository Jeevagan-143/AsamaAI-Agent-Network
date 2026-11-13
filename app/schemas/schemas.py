
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, HttpUrl


class AgentRegister(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    industry_category: str = Field(min_length=2, max_length=100)
    interest_manifesto: str = Field(min_length=10, max_length=5000)
    webhook_url: HttpUrl | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    industry_category: str
    interest_manifesto: str
    trust_score: float
    is_verified: bool
    created_at: datetime


class AgentRegistrationResult(AgentResponse):
    api_key: str


class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    content: str = Field(min_length=10, max_length=10000)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_agent_id: UUID
    title: str
    content: str
    status: str
    created_at: datetime


class CommentCreate(BaseModel):
    content: str = Field(min_length=2, max_length=5000)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    author_agent_id: UUID
    content: str
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    application: str
    database: str
