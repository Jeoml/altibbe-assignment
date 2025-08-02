"""
FastAPI main application and API endpoints
"""

import json
import uuid
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import TRANSPARENCY_QUESTIONS
from database import get_db, Product, AssessmentSession
from schemas import ProductCreate, QuestionResponse, AssessmentResult
from services import register_product, process_response
from auth import verify_token
from report_generator import HtmlReportGenerator

# FastAPI App
app = FastAPI(title="Product Transparency Assessment API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.post("/api/products/register")
async def register_product_endpoint(
    product: ProductCreate,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Register a new product for assessment"""
    try:
        result = register_product(
            company_name=product.company_name,
            product_name=product.product_name,
            product_id=product.product_id,
            description=product.description,
            domain=product.domain
        )
        
        # Create assessment session
        session_id = str(uuid.uuid4())
        session = AssessmentSession(
            session_id=session_id,
            product_id=product.product_id,
            questions_data=json.dumps(TRANSPARENCY_QUESTIONS),
            responses="[]",
            scores="[]"
        )
        
        db.add(session)
        db.commit()
        
        return {
            "status": "success",
            "session_id": session_id,
            "product_id": product.product_id,
            "first_question": TRANSPARENCY_QUESTIONS[0],
            "remaining_questions": TRANSPARENCY_QUESTIONS[1:],  # Questions 2-6
            "message": "Product registered. Assessment started."
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/assessment/respond", response_model=AssessmentResult)
async def submit_response(
    response: QuestionResponse,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Submit response to current question and get remaining questions"""
    try:
        result = process_response(
            session_id=response.session_id,
            user_message=response.message,
            context=response.context or {}
        )
        
        assessment_result = AssessmentResult(
            answer=result["answer"],
            score=result["score"],
            question_number=result["question_number"],
            session_id=response.session_id,
            is_complete=result.get("is_complete", False)
        )
        
        if result.get("final_score"):
            assessment_result.final_score = result["final_score"]
        
        if result.get("all_scores"):
            assessment_result.all_scores = result["all_scores"]
        
        # Add remaining questions if not complete
        if not assessment_result.is_complete and "remaining_questions" in result:
            assessment_result.remaining_questions = result["remaining_questions"]
            
        return assessment_result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/assessment/{session_id}/status")
async def get_assessment_status(
    session_id: str,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get current assessment status"""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "current_question": session.current_question,
        "status": session.status,
        "final_score": session.final_score,
        "responses_count": len(json.loads(session.responses or "[]")),
        "next_question": TRANSPARENCY_QUESTIONS[session.current_question - 1] if session.current_question <= 6 else None
    }

@app.get("/api/assessment/{session_id}/report")
async def get_assessment_report(
    session_id: str,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get detailed assessment report with LaTeX summary"""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get product information
    product = db.query(Product).filter(
        Product.product_id == session.product_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    responses = json.loads(session.responses or "[]")
    scores = json.loads(session.scores or "[]")
    
    # Prepare product data for LaTeX generation
    product_data = {
        "company_name": product.company_name,
        "product_name": product.product_name,
        "product_id": product.product_id,
        "description": product.description,
        "domain": product.domain
    }
    
    session_data = {
        "session_id": session_id,
        "status": session.status,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "current_question": session.current_question
    }
    
    # Generate LaTeX report using LLM
    try:
        latex_report = HtmlReportGenerator.generate_transparency_report(
            product_data=product_data,
            session_data=session_data,
            responses=responses,
            scores=scores,
            final_score=session.final_score or 0.0
        )
    except Exception as e:
        print(f"Error generating LaTeX report: {e}")
        latex_report = "Error generating LaTeX report. Please try again later."
    
    return {
        "session_id": session_id,
        "product_id": session.product_id,
        "status": session.status,
        "final_score": session.final_score,
        "detailed_responses": responses,
        "scores": scores,
        "created_at": session.created_at,
        "completed_at": session.updated_at if session.status == "completed" else None,
        "latex_report": latex_report  # New field with LaTeX transparency report
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)