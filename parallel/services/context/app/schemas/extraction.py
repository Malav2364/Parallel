from pydantic import BaseModel, Field


class ContextExtraction(BaseModel):
    """Structured durable-context updates proposed by Gemini.

    Lives in the schema layer (not the extractor service) so it can be composed
    into ``UnderstandingResult`` without pulling a service import into the schema
    package. The merged understanding call returns this alongside the decision;
    the standalone ``ContextExtractor`` still returns it on the Tier-1 paths.
    """

    updates: dict = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)
    reasoning: str = ""
