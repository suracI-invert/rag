from uuid import uuid4

from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    id: str = Field(str(uuid4()))
    content: str | None
