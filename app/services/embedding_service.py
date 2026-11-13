
from functools import lru_cache
from typing import List

from fastembed import TextEmbedding

from app.core.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    """Load and cache the local FastEmbed model."""
    return TextEmbedding(
        model_name=settings.EMBEDDING_MODEL
    )


def generate_embedding(text: str) -> List[float]:
    """Generate a normalized semantic embedding for text."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    model = get_embedding_model()

    embeddings = list(model.embed([text.strip()]))

    if not embeddings:
        raise RuntimeError("Embedding model returned no result.")

    vector = embeddings[0].tolist()

    if len(vector) != settings.EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Expected {settings.EMBEDDING_DIMENSIONS} dimensions, "
            f"but received {len(vector)}."
        )

    return vector


def generate_agent_embedding(
    company_name: str,
    industry_category: str,
    interest_manifesto: str,
) -> List[float]:
    """Generate an embedding representing an agent's interests."""
    combined_text = (
        f"Company: {company_name}. "
        f"Industry: {industry_category}. "
        f"Interests and capabilities: {interest_manifesto}"
    )

    return generate_embedding(combined_text)


def generate_post_embedding(
    title: str,
    content: str,
) -> List[float]:
    """Generate an embedding representing a published post."""
    combined_text = (
        f"Post title: {title}. "
        f"Post content: {content}"
    )

    return generate_embedding(combined_text)
