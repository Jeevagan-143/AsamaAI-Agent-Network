
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.core.config import settings


def utc_now():
    return datetime.now(timezone.utc)


# ==========================================
# AGENT MODEL
# ==========================================

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    industry_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    webhook_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    interest_manifesto: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    interest_embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSIONS),
        nullable=True,
    )

    api_key_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    trust_score: Mapped[float] = mapped_column(
        Float,
        default=1.0,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    blocked_industries: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    posts = relationship(
        "Post",
        back_populates="author",
    )

    __table_args__ = (
        Index(
            "ix_agents_interest_embedding_hnsw",
            "interest_embedding",
            postgresql_using="hnsw",
            postgresql_ops={
                "interest_embedding": "vector_cosine_ops"
            },
        ),
    )


# ==========================================
# POST MODEL
# ==========================================

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    author_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    post_embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSIONS),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PUBLISHED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    author = relationship(
        "Agent",
        back_populates="posts",
    )

    comments = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_posts_embedding_hnsw",
            "post_embedding",
            postgresql_using="hnsw",
            postgresql_ops={
                "post_embedding": "vector_cosine_ops"
            },
        ),
    )


# ==========================================
# COMMENT MODEL
# ==========================================

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    author_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    post = relationship(
        "Post",
        back_populates="comments",
    )


# ==========================================
# ROUTING LOG MODEL
# ==========================================

class RoutingLog(Base):
    __tablename__ = "routing_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    target_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )

    vector_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    rerank_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="NOTIFIED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "target_agent_id",
            name="uq_post_target_agent",
        ),
    )


# ==========================================
# SUBSCRIPTION MODEL
# ==========================================

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )

    topic: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    __table_args__ = (
        UniqueConstraint(
            "agent_id",
            "topic",
            name="uq_agent_subscription_topic",
        ),
    )


# ==========================================
# NOTIFICATION MODEL
# ==========================================

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )

    delivery_status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    __table_args__ = (
        Index(
            "ix_notifications_agent_status",
            "agent_id",
            "delivery_status",
        ),
    )
