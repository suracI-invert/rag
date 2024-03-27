from uuid import uuid4

from pydantic import BaseModel, Field

class QueryBase(BaseModel):
    text: str | None = None

class QueryRequest(QueryBase):
    pass

class QueryProcessed(QueryBase):
    id: str = Field(str(uuid4()))

class DocumentBase(BaseModel):
    text: str | None = None

class DocumentUpload(DocumentBase):
    pass

class DocumentProcessed(DocumentBase):
    id: str = Field(str(uuid4()))
