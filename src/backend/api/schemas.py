from typing import Literal

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description=(
            "Learner programming question to retrieve "
            "relevant source chunks for."
        ),
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Maximum number of chunks to retrieve.",
    )
    min_similarity_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum similarity score required for returned chunks."
        ),
    )


class RetrievedChunkResponse(BaseModel):
    rank: int
    chunk_id: str
    source: str
    text_preview: str
    distance: float
    similarity_score: float


class RetrieveResponse(BaseModel):
    query: str
    chunks_returned: int
    results: list[RetrievedChunkResponse]


class AskRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description=(
            "Learner programming question to answer using "
            "source-grounded RAG."
        ),
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description=(
            "Maximum number of source chunks to use "
            "for answer generation."
        ),
    )
    min_similarity_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum similarity score required before "
            "generating an answer."
        ),
    )
    response_mode: Literal["auto", "answer", "hint"] = Field(
        default="auto",
        description=(
            "Response mode. Auto detects natural-language "
            "hint requests."
        ),
    )
    hint_level: int = Field(
        default=1,
        ge=1,
        le=3,
        description=(
            "Hint detail level used when response_mode resolves to hint."
        ),
    )


class AnswerSourceResponse(BaseModel):
    source_id: str
    chunk_id: str
    source: str
    similarity_score: float
    text_preview: str


class AskResponse(BaseModel):
    query: str
    answer_status: str
    answer: str
    sources: list[AnswerSourceResponse]
