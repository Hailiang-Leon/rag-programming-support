from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Learner question to retrieve relevant source chunks for.",
        examples=["What is a variable in Python?"],
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Maximum number of chunks to retrieve.",
        examples=[3],
    )
    min_similarity_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score required for a retrieved chunk.",
        examples=[0.35],
    )


class RetrievedChunkResponse(BaseModel):
    rank: int
    chunk_id: str
    source: str
    similarity_score: float
    distance: float
    text_preview: str


class RetrieveResponse(BaseModel):
    query: str
    chunks_returned: int
    results: list[RetrievedChunkResponse]