from typing import Optional, Union
from pydantic import BaseModel

class Entities(BaseModel):
    document_name: Optional[str] = None
    search_query: Optional[str] = None
    document_type: Optional[str] = None
    page_number: Optional[Union[int, str]] = None 
    navigation_direction: Optional[str] = None
    reading_action: Optional[str] = None
    summary_type: Optional[str] = None
    question: Optional[str] = None
    study_aid_type: Optional[str] = None

class NLUResult(BaseModel):
    intent: str
    confidence: float
    entities: Entities
    needs_clarification: bool