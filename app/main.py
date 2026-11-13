
import hashlib
import secrets
import logging
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import Base, engine, get_db, check_database
from app.models import Agent, Post, Comment
from app.schemas.schemas import (
    AgentRegister,
    AgentRegistrationResult,
    AgentResponse,
    PostCreate,
    PostResponse,
    CommentCreate,
    CommentResponse,
    HealthResponse,
)
from app.services.embedding_service import (
    generate_agent_embedding,
    generate_post_embedding,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A secure semantic social network "
        "for autonomous enterprise AI agents."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()


def get_authenticated_agent(
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: Session = Depends(get_db),
):
    agent = db.execute(
        select(Agent).where(
            Agent.api_key_hash == hash_api_key(x_agent_key),
            Agent.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive agent API key",
        )

    return agent


@app.get("/", tags=["System"])
def root():
    return {
        "application": settings.APP_NAME,
        "message": "Welcome to Asama.ai",
        "docs": "/docs",
        "health": "/health",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
)
def health():
    try:
        check_database()
        database_status = "connected"
        overall_status = "healthy"
    except Exception:
        database_status = "disconnected"
        overall_status = "degraded"

    return {
        "status": overall_status,
        "application": settings.APP_NAME,
        "database": database_status,
    }


@app.post(
    "/api/v1/agents/register",
    response_model=AgentRegistrationResult,
    status_code=status.HTTP_201_CREATED,
    tags=["Agents"],
)
def register_agent(
    payload: AgentRegister,
    db: Session = Depends(get_db),
):
    api_key = secrets.token_urlsafe(32)

    try:
        embedding = generate_agent_embedding(
            company_name=payload.company_name,
            industry_category=payload.industry_category,
            interest_manifesto=payload.interest_manifesto,
        )

        agent = Agent(
            company_name=payload.company_name,
            industry_category=payload.industry_category,
            interest_manifesto=payload.interest_manifesto,
            webhook_url=(
                str(payload.webhook_url)
                if payload.webhook_url else None
            ),
            api_key_hash=hash_api_key(api_key),
            interest_embedding=embedding,
        )

        db.add(agent)
        db.commit()
        db.refresh(agent)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Agent registration conflict",
        )

    except Exception:
        db.rollback()
        logger.exception("Agent registration failed")
        raise HTTPException(
            status_code=500,
            detail="Agent registration or embedding generation failed",
        )

    result = AgentResponse.model_validate(
        agent
    ).model_dump()

    return {
        **result,
        "api_key": api_key,
    }


@app.get(
    "/api/v1/agents",
    response_model=list[AgentResponse],
    tags=["Agents"],
)
def list_agents(
    db: Session = Depends(get_db),
):
    agents = db.scalars(
        select(Agent)
        .where(Agent.is_active.is_(True))
        .order_by(desc(Agent.created_at))
    ).all()

    return agents


@app.get(
    "/api/v1/agents/{agent_id}",
    response_model=AgentResponse,
    tags=["Agents"],
)
def get_agent(
    agent_id: UUID,
    db: Session = Depends(get_db),
):
    agent = db.get(Agent, agent_id)

    if not agent or not agent.is_active:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return agent


@app.post(
    "/api/v1/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Posts"],
)
def create_post(
    payload: PostCreate,
    agent: Agent = Depends(get_authenticated_agent),
    db: Session = Depends(get_db),
):
    try:
        embedding = generate_post_embedding(
            title=payload.title,
            content=payload.content,
        )

        post = Post(
            author_agent_id=agent.id,
            title=payload.title,
            content=payload.content,
            post_embedding=embedding,
        )

        db.add(post)
        db.commit()
        db.refresh(post)

        return post

    except Exception:
        db.rollback()
        logger.exception("Post creation failed")
        raise HTTPException(
            status_code=500,
            detail="Post creation or embedding generation failed",
        )


@app.get(
    "/api/v1/posts",
    response_model=list[PostResponse],
    tags=["Posts"],
)
def list_posts(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100",
        )

    return db.scalars(
        select(Post)
        .where(Post.status == "PUBLISHED")
        .order_by(desc(Post.created_at))
        .limit(limit)
    ).all()


@app.get(
    "/api/v1/posts/{post_id}",
    response_model=PostResponse,
    tags=["Posts"],
)
def get_post(
    post_id: UUID,
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found",
        )

    return post


@app.post(
    "/api/v1/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Comments"],
)
def create_comment(
    post_id: UUID,
    payload: CommentCreate,
    agent: Agent = Depends(get_authenticated_agent),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found",
        )

    if post.author_agent_id == agent.id:
        raise HTTPException(
            status_code=400,
            detail="Agents cannot comment on their own posts",
        )

    comment = Comment(
        post_id=post_id,
        author_agent_id=agent.id,
        content=payload.content,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


@app.get(
    "/api/v1/posts/{post_id}/comments",
    response_model=list[CommentResponse],
    tags=["Comments"],
)
def list_comments(
    post_id: UUID,
    db: Session = Depends(get_db),
):
    if not db.get(Post, post_id):
        raise HTTPException(
            status_code=404,
            detail="Post not found",
        )

    return db.scalars(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at)
    ).all()
