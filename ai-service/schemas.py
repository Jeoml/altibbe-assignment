"""
Pydantic models for request/response validation
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    company_name: str = Field(..., description="Name of the company")
    product_name: str = Field(..., description="Name of the product")
    product_id: str = Field(..., description="Unique product identifier")
    description: str = Field(..., description="Description of the product")
    domain: str = Field(..., description="Domain/category of the product")

class QuestionResponse(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict] = None

class MultipleQuestionResponse(BaseModel):
    session_id: str
    responses: List[str] = Field(..., description="List of responses to remaining questions")
    context: Optional[Dict] = None

class AssessmentResult(BaseModel):
    answer: str
    score: int
    question_number: int
    session_id: str
    is_complete: bool = False
    final_score: Optional[float] = None
    remaining_questions: Optional[List[str]] = None
    all_scores: Optional[List[int]] = None