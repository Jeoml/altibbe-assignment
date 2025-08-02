"""
Business logic and service layer functions
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List

from database import SessionLocal, Product, AssessmentSession
from config import TRANSPARENCY_QUESTIONS
from scoring import TransparencyScorer

def register_product(company_name: str, product_name: str, product_id: str, 
                    description: str, domain: str) -> Dict:
    """Register product in database"""
    db = SessionLocal()
    try:
        # Check if product already exists
        existing = db.query(Product).filter(Product.product_id == product_id).first()
        if existing:
            raise ValueError(f"Product with ID {product_id} already exists")
        
        # Create new product
        product = Product(
            id=str(uuid.uuid4()),
            company_name=company_name,
            product_name=product_name,
            product_id=product_id,
            description=description,
            domain=domain
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return {
            "status": "success",
            "product_id": product_id,
            "message": f"Product '{product_name}' registered successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to register product: {str(e)}")
    finally:
        db.close()

def process_response(session_id: str, user_message: str, context: Dict = None) -> Dict:
    """Process user response and return next question or completion"""
    
    db = SessionLocal()
    try:
        # Get session
        session = db.query(AssessmentSession).filter(
            AssessmentSession.session_id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Parse stored data
        responses = json.loads(session.responses or "[]")
        scores = json.loads(session.scores or "[]")
        
        current_q = session.current_question
        
        if current_q > 6:
            return {
                "status": "completed",
                "message": "Assessment already completed",
                "final_score": session.final_score
            }
        
        # Score current response
        question = TRANSPARENCY_QUESTIONS[current_q - 1]
        score = TransparencyScorer.score_response(question, user_message, current_q)
        
        # Store response and score
        responses.append({
            "question_number": current_q,
            "question": question,
            "response": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        scores.append(score)
        
        # Update session
        session.responses = json.dumps(responses)
        session.scores = json.dumps(scores)
        session.current_question = current_q + 1
        session.updated_at = datetime.utcnow()
        
        # Check if assessment is complete
        if current_q >= 6:
            final_score = sum(scores) / len(scores)
            session.final_score = final_score
            session.status = "completed"
            
            db.commit()
            
            return {
                "status": "completed",
                "answer": user_message,
                "score": score,
                "question_number": current_q,
                "final_score": final_score,
                "is_complete": True,
                "all_scores": scores
            }
        else:
            db.commit()
            
            # Return all remaining questions
            remaining_questions = TRANSPARENCY_QUESTIONS[current_q:]
            return {
                "status": "continue",
                "answer": user_message,
                "score": score,
                "question_number": current_q,
                "remaining_questions": remaining_questions,
                "is_complete": False,
                "all_scores": scores
            }
            
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to process response: {str(e)}")
    finally:
        db.close()

def process_multiple_responses(session_id: str, responses_list: List[str], context: Dict = None) -> Dict:
    """Process multiple user responses in sequence and return final assessment"""
    
    db = SessionLocal()
    try:
        # Get session
        session = db.query(AssessmentSession).filter(
            AssessmentSession.session_id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Parse stored data
        stored_responses = json.loads(session.responses or "[]")
        scores = json.loads(session.scores or "[]")
        
        current_q = session.current_question
        
        if current_q > 6:
            return {
                "status": "completed",
                "message": "Assessment already completed",
                "final_score": session.final_score
            }
        
        # Process all remaining responses
        for i, user_message in enumerate(responses_list):
            if current_q + i > 6:
                break
                
            question_num = current_q + i
            question = TRANSPARENCY_QUESTIONS[question_num - 1]
            score = TransparencyScorer.score_response(question, user_message, question_num)
            
            # Store response and score
            stored_responses.append({
                "question_number": question_num,
                "question": question,
                "response": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            scores.append(score)
        
        # Calculate how many questions were processed
        questions_processed = min(len(responses_list), 6 - current_q + 1)
        new_current_q = current_q + questions_processed
        
        # Update session
        session.responses = json.dumps(stored_responses)
        session.scores = json.dumps(scores)
        session.current_question = new_current_q
        session.updated_at = datetime.utcnow()
        
        # Check if assessment is complete
        if new_current_q > 6:
            final_score = sum(scores) / len(scores)
            session.final_score = final_score
            session.status = "completed"
            
            db.commit()
            
            return {
                "status": "completed",
                "final_score": final_score,
                "is_complete": True,
                "all_scores": scores,
                "total_questions_answered": len(scores)
            }
        else:
            db.commit()
            
            # Return remaining questions if any
            remaining_questions = TRANSPARENCY_QUESTIONS[new_current_q - 1:] if new_current_q <= 6 else []
            return {
                "status": "continue",
                "remaining_questions": remaining_questions,
                "is_complete": False,
                "all_scores": scores,
                "questions_answered": questions_processed,
                "next_question_number": new_current_q
            }
            
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to process multiple responses: {str(e)}")
    finally:
        db.close()