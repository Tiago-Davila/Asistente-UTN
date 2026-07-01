"""
rag/domain/queries.py — User query and assistant answer domain models.

Traceability:
  UserQuery      → FR-001, FR-002, FR-009, data-model.md §UserQuery
  CitedSource    → FR-005, data-model.md §CitedSource
  AssistantAnswer → FR-006, FR-007, FR-008, data-model.md §AssistantAnswer
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from rag.domain.enums import AreaInstitucional

# Approved refusal text — must match rules.REFUSAL_TEXT exactly (FR-007).
_REFUSAL_TEXT = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)

# Maximum question length — must match settings.max_question_length default (FR-002).
_MAX_QUESTION_LENGTH = 2000

# Maximum retrieval count — data-model.md §UserQuery.
_MAX_RESULTS = 10


class UserQuery(BaseModel):
    """A question submitted by a user or administrator-facing process.

    data-model.md §UserQuery.
    """

    question: str = Field(
        ...,
        description="User question text (non-empty, ≤ MAX_QUESTION_LENGTH characters).",
    )
    area_filter: Optional[AreaInstitucional] = Field(
        default=None,
        description="Optional institutional area filter (FR-009).",
    )
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    max_results: Optional[int] = Field(
        default=None,
        ge=1,
        le=_MAX_RESULTS,
        description=f"Requested result count; bounded at {_MAX_RESULTS}.",
    )

    @field_validator("question")
    @classmethod
    def question_must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "question must be non-empty after trimming whitespace (FR-002)"
            )
        return v

    @field_validator("question")
    @classmethod
    def question_within_length_limit(cls, v: str) -> str:
        if len(v) > _MAX_QUESTION_LENGTH:
            raise ValueError(
                f"question must not exceed {_MAX_QUESTION_LENGTH} characters (FR-002); "
                f"got {len(v)}"
            )
        return v


class CitedSource(BaseModel):
    """Source information shown to the user in an answer.

    data-model.md §CitedSource.
    """

    url: str = Field(..., description="Institutional source URL (required).")
    title: Optional[str] = Field(
        default=None, description="Page title when available (FR-005)."
    )
    area: Optional[AreaInstitucional] = Field(default=None)
    regional: Optional[str] = Field(default=None)
    department: Optional[str] = Field(default=None)

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("CitedSource url must not be empty")
        return v


class AssistantAnswer(BaseModel):
    """The response returned to the user.

    data-model.md §AssistantAnswer.
    Validation rules:
      - If context_sufficient is False, answer must use the approved refusal text.
      - If context_sufficient is True, sources must be non-empty.
      - answer must not cite sources outside retrieved context (enforced in rules.py).
    """

    answer: str = Field(
        ..., description="Generated answer text or approved refusal text."
    )
    sources: list[CitedSource] = Field(default_factory=list)
    context_sufficient: bool = Field(default=False)
    error: Optional[dict[str, Any]] = Field(
        default=None,
        description="Structured error payload when the service cannot answer.",
    )

    @model_validator(mode="after")
    def validate_answer_consistency(self) -> "AssistantAnswer":
        if not self.context_sufficient and self.error is None:
            if self.answer != _REFUSAL_TEXT:
                raise ValueError(
                    "When context_sufficient is False and no error is set, "
                    "answer must be the approved refusal text (FR-007)"
                )
        if self.context_sufficient and not self.sources:
            raise ValueError(
                "When context_sufficient is True, sources must include at least "
                "one URL (FR-005)"
            )
        return self
