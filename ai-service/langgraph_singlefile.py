"""
Product Transparency Assessment Agent using LangGraph, Groq, and FastAPI
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Annotated
from dataclasses import dataclass, asdict
from enum import Enum

import asyncio
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Database imports (using SQLAlchemy)
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID

# Patch for CockroachDB version detection
import sqlalchemy.dialects.postgresql.base as postgresql_base
original_get_server_version_info = postgresql_base.PGDialect._get_server_version_info

def patched_get_server_version_info(self, connection):
    """Patched version to handle CockroachDB version strings"""
    try:
        return original_get_server_version_info(self, connection)
    except AssertionError as e:
        if "CockroachDB" in str(e):
            # Return a fake PostgreSQL version for CockroachDB
            return (13, 0, 0)  # PostgreSQL 13 compatible
        raise

postgresql_base.PGDialect._get_server_version_info = patched_get_server_version_info

# LangGraph imports - Updated for newer versions
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# Groq imports
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./transparency_assessment.db")

# Create engine with appropriate settings
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    product_id = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=False)
    domain = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, nullable=False)
    current_question = Column(Integer, default=1)
    questions_data = Column(Text)  # JSON string
    responses = Column(Text)  # JSON string
    scores = Column(Text)  # JSON string
    final_score = Column(Float, default=0.0)
    status = Column(String, default="active")  # active, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
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

# Agent State - Updated for LangGraph
class State(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str
    product_id: str
    current_question: int
    questions: List[str]
    responses: List[str]
    scores: List[int]
    context: Dict[str, Any]
    final_score: float
    is_complete: bool

# Indian Consumer Safety Guidelines Questions
TRANSPARENCY_QUESTIONS = [
    "Please provide detailed information about all ingredients/components used in your product. Are there any potentially harmful substances that consumers should be aware of?",
    
    "What quality control measures and testing procedures do you implement during manufacturing? Please share your quality certifications and compliance standards.",
    
    "Are there any known side effects, risks, or contraindications associated with your product? How do you communicate these to consumers?",
    
    "Please describe your product's environmental impact and disposal methods. What sustainable practices do you follow in production?",
    
    "What is your product's shelf life, storage requirements, and proper usage instructions? How do you ensure consumers receive accurate information?",
    
    "Do you have a system for tracking adverse events, consumer complaints, and product recalls? How transparent are you about product issues and their resolution?"
]

# Groq Client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Scoring System
class TransparencyScorer:
    @staticmethod
    def score_response(question: str, response: str, question_number: int) -> int:
        """Score response based on transparency criteria"""
        
        scoring_prompt = f"""
        As an expert in Indian consumer safety regulations with deep knowledge of BIS standards, FSSAI guidelines, Consumer Protection Act 2019, Drug Controller regulations, and industry best practices, conduct a thorough analytical evaluation of this transparency response.

        Question {question_number}: {question}
        Response: {response}

        ANALYTICAL FRAMEWORK - Reason through each element systematically:

        1. COMPLETENESS OF INFORMATION (30 points) - Deep Analysis Required:
           
           a) COMPREHENSIVENESS ASSESSMENT:
              - Analyze if EVERY component of the question is addressed
              - Evaluate depth vs breadth of information provided
              - Check for any missing critical elements that consumers need
              - Assess if technical details are sufficiently detailed
           
           b) QUANTITATIVE DATA EVALUATION:
              - Examine specificity of numbers, percentages, concentrations
              - Verify if measurement units are provided
              - Check if ranges or exact values are given where appropriate
              - Assess statistical significance of any claims made
           
           c) REGULATORY DOCUMENTATION ANALYSIS:
              - Identify specific certifications mentioned (ISO numbers, BIS codes, FSSAI license numbers)
              - Evaluate validity and relevance of cited standards
              - Check if regulatory compliance is evidenced with documentation
              - Assess currency and authenticity of regulatory references

        2. HONESTY AND TRANSPARENCY (25 points) - Behavioral Analysis Required:
           
           a) LIMITATION ACKNOWLEDGMENT ASSESSMENT:
              - Analyze whether response admits knowledge gaps or uncertainties
              - Evaluate if caveats are provided where appropriate
              - Check for honest disclosure of product limitations
              - Assess balance between confidence and humility in claims
           
           b) RISK DISCLOSURE EVALUATION:
              - Examine completeness of negative aspect disclosure
              - Analyze severity and probability of disclosed risks
              - Check if risk mitigation strategies are provided
              - Evaluate comparative risk assessment with alternatives
           
           c) COMMUNICATION TONE ANALYSIS:
              - Distinguish between factual reporting vs marketing language
              - Analyze use of qualifiers vs absolute statements
              - Check for evidence-based claims vs promotional assertions
              - Evaluate objectivity in presenting information

        3. COMPLIANCE WITH INDIAN CONSUMER SAFETY GUIDELINES (25 points) - Regulatory Analysis Required:
           
           a) SPECIFIC REGULATION CITATION ANALYSIS:
              - Identify exact regulatory frameworks mentioned (BIS Act 2016, FSSAI Act 2006, etc.)
              - Evaluate accuracy of regulatory interpretations
              - Check for industry-specific compliance requirements
              - Assess understanding of mandatory vs voluntary standards
           
           b) CONSUMER PROTECTION ALIGNMENT:
              - Analyze adherence to Consumer Protection Act 2019 disclosure requirements
              - Evaluate right-to-information compliance
              - Check for consumer grievance mechanism alignment
              - Assess product liability law considerations
           
           c) ENFORCEMENT EVIDENCE EVALUATION:
              - Examine proof of regulatory compliance (license numbers, certificates)
              - Analyze third-party verification mentions
              - Check for audit trail references
              - Evaluate regulatory body interaction evidence

        4. CLARITY AND ACCESSIBILITY (20 points) - Communication Analysis Required:
           
           a) LANGUAGE ACCESSIBILITY ASSESSMENT:
              - Analyze technical jargon usage and explanations provided
              - Evaluate sentence complexity and readability
              - Check for multilingual considerations if relevant
              - Assess cultural sensitivity in communication
           
           b) ACTIONABILITY EVALUATION:
              - Examine specific instructions provided to consumers
              - Analyze step-by-step guidance clarity
              - Check for decision-making support information
              - Evaluate emergency response instructions if applicable
           
           c) SAFETY COMMUNICATION ANALYSIS:
              - Assess prominence of critical safety information
              - Analyze warning placement and visibility
              - Check for risk severity communication effectiveness
              - Evaluate precautionary measure clarity

        REASONING METHODOLOGY:
        - Consider the specific domain context (food/pharma/electronics/cosmetics)
        - Analyze response against question-specific expectations
        - Evaluate information hierarchy and prioritization
        - Consider consumer impact and decision-making utility
        - Assess legal liability and regulatory risk implications

        SCORING CALIBRATION:
        - 95-100: Exceptional transparency exceeding regulatory requirements with comprehensive reasoning
        - 85-94: Strong transparency meeting all regulatory standards with good reasoning
        - 75-84: Adequate transparency with basic regulatory compliance and some reasoning gaps
        - 65-74: Minimal transparency with significant reasoning deficiencies
        - Below 65: Inadequate transparency with poor reasoning and compliance failures

        After conducting this comprehensive analysis across all dimensions, provide only the final numerical score (1-100) that reflects the depth of reasoning demonstrated in the response.
        """
        
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",  # Upgraded to 70B for better reasoning
                messages=[{"role": "user", "content": scoring_prompt}],
                temperature=0.1,  # Very low temperature for consistent analytical reasoning
                max_tokens=50  # Increased for detailed reasoning analysis
            )
            
            score_text = completion.choices[0].message.content.strip()
            score = int(''.join(filter(str.isdigit, score_text)))
            return max(1, min(100, score))  # Ensure score is between 1-100
            
        except Exception as e:
            print(f"Error scoring response: {e}")
            return 50  # Default moderate score on error

# LaTeX Report Generator
class HtmlReportGenerator:
    @staticmethod
    def generate_transparency_report(
        product_data: Dict,
        session_data: Dict,
        responses: List[Dict],
        scores: List[int],
        final_score: float
    ) -> str:
        """Generate a comprehensive LaTeX transparency report using LLM"""
        
        # Prepare data for LLM processing
        assessment_data = {
            "product": product_data,
            "session": session_data,
            "responses": responses,
            "scores": scores,
            "final_score": final_score,
            "questions": TRANSPARENCY_QUESTIONS
        }
        
        report_generation_prompt = f"""
        As a professional regulatory compliance expert and technical writer, generate a comprehensive LaTeX transparency assessment report based on the following product assessment data:

        ASSESSMENT DATA:
        {json.dumps(assessment_data, indent=2, default=str)}

        REPORT REQUIREMENTS:

        1. DOCUMENT STRUCTURE:
           - Professional academic/regulatory report format
           - Clear sections with proper LaTeX formatting
           - Include title page, executive summary, detailed analysis, and recommendations
           - Use appropriate LaTeX packages and formatting commands

        2. CONTENT SECTIONS TO INCLUDE:
           a) Title Page with product details and assessment metadata
           b) Executive Summary (key findings and overall transparency score)
           c) Assessment Methodology overview
           d) Detailed Analysis for each transparency dimension:
              - Ingredient/Component Transparency
              - Quality Control & Certifications
              - Risk Communication & Safety
              - Environmental Impact & Sustainability
              - Product Information & Usage Guidelines
              - Complaint Management & Recall Systems
           e) Scoring Analysis with visual elements (tables, charts if applicable)
           f) Regulatory Compliance Assessment
           g) Recommendations for Improvement
           h) Conclusion

        3. FORMATTING REQUIREMENTS:
           - Use proper LaTeX document class (article or report)
           - Include necessary packages (geometry, fancyhdr, graphicx, booktabs, etc.)
           - Professional fonts and spacing
           - Proper section numbering and cross-references
           - Tables for scoring breakdown
           - Professional color scheme if applicable

        4. CONTENT QUALITY:
           - Objective, data-driven analysis
           - Cite specific regulatory frameworks (BIS, FSSAI, Consumer Protection Act)
           - Include specific quotes from responses where relevant
           - Professional tone throughout
           - Actionable recommendations based on assessment findings

        5. TECHNICAL ELEMENTS:
           - Properly escaped LaTeX special characters
           - Valid LaTeX syntax throughout
           - Include document metadata
           - Proper bibliography format if references are included

        Generate a complete, compilable LaTeX document that serves as a professional transparency assessment report. The report should be comprehensive enough to be used for regulatory compliance, consumer information, or business improvement purposes.

        Return ONLY the LaTeX code, starting with \\documentclass and ending with \\end{{document}}.
        """
        
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": report_generation_prompt}],
                temperature=0.2,  # Low temperature for consistent, professional output
                max_tokens=4000  # Allow for comprehensive report generation
            )
            
            latex_report = completion.choices[0].message.content.strip()
            
            # Clean up the LaTeX code to ensure it's properly formatted
            if not latex_report.startswith("\\documentclass"):
                # If the response doesn't start with documentclass, try to extract LaTeX code
                lines = latex_report.split('\n')
                latex_start = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith("\\documentclass"):
                        latex_start = i
                        break
                
                if latex_start >= 0:
                    latex_report = '\n'.join(lines[latex_start:])
            
            return latex_report
            
        except Exception as e:
            print(f"Error generating LaTeX report: {e}")
            # Return a basic LaTeX template as fallback
            return HtmlReportGenerator._generate_fallback_report(
                product_data, session_data, responses, scores, final_score
            )
    
    @staticmethod
    def _generate_fallback_report(
        product_data: Dict,
        session_data: Dict,
        responses: List[Dict],
        scores: List[int],
        final_score: float
    ) -> str:
        """Generate a basic LaTeX report as fallback"""
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        latex_template = f"""\\documentclass[12pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{fancyhdr}}
\\usepackage{{booktabs}}
\\usepackage{{graphicx}}
\\usepackage{{xcolor}}
\\usepackage{{titlesec}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\rhead{{Transparency Assessment Report}}
\\lhead{{Product: {product_data.get('product_name', 'N/A')}}}
\\cfoot{{\\thepage}}

\\title{{\\textbf{{Product Transparency Assessment Report}}}}
\\author{{Automated Assessment System}}
\\date{{{current_date}}}

\\begin{{document}}

\\maketitle

\\section{{Executive Summary}}
This report presents the transparency assessment results for \\textbf{{{product_data.get('product_name', 'N/A')}}} manufactured by \\textbf{{{product_data.get('company_name', 'N/A')}}}. The assessment was conducted based on Indian consumer safety guidelines and regulatory compliance standards.

\\textbf{{Overall Transparency Score: {final_score:.1f}/100}}

\\section{{Product Information}}
\\begin{{itemize}}
    \\item \\textbf{{Product Name:}} {product_data.get('product_name', 'N/A')}
    \\item \\textbf{{Company:}} {product_data.get('company_name', 'N/A')}
    \\item \\textbf{{Product ID:}} {product_data.get('product_id', 'N/A')}
    \\item \\textbf{{Domain:}} {product_data.get('domain', 'N/A')}
    \\item \\textbf{{Assessment Date:}} {session_data.get('created_at', 'N/A')}
\\end{{itemize}}

\\section{{Assessment Results}}
The assessment evaluated six key areas of product transparency:

\\begin{{table}}[h]
\\centering
\\begin{{tabular}}{{lc}}
\\toprule
\\textbf{{Assessment Area}} & \\textbf{{Score}} \\\\
\\midrule"""

        # Add scores for each question
        question_areas = [
            "Ingredient/Component Information",
            "Quality Control & Certifications", 
            "Risk Communication & Safety",
            "Environmental Impact",
            "Product Information & Usage",
            "Complaint Management Systems"
        ]
        
        for i, score in enumerate(scores):
            if i < len(question_areas):
                latex_template += f"\n{question_areas[i]} & {score} \\\\"
        
        latex_template += f"""
\\midrule
\\textbf{{Overall Score}} & \\textbf{{{final_score:.1f}}} \\\\
\\bottomrule
\\end{{tabular}}
\\caption{{Transparency Assessment Scores}}
\\end{{table}}

\\section{{Detailed Analysis}}
The assessment revealed the following key findings:

\\subsection{{Strengths}}
Areas where the product demonstrated good transparency practices.

\\subsection{{Areas for Improvement}}
Recommendations for enhancing product transparency and regulatory compliance.

\\section{{Regulatory Compliance}}
This assessment was conducted in accordance with:
\\begin{{itemize}}
    \\item Consumer Protection Act 2019
    \\item Bureau of Indian Standards (BIS) guidelines
    \\item Food Safety and Standards Authority of India (FSSAI) regulations
    \\item Industry-specific regulatory requirements
\\end{{itemize}}

\\section{{Conclusion}}
Based on the comprehensive assessment, the product achieved a transparency score of {final_score:.1f} out of 100. This report serves as a baseline for transparency improvements and regulatory compliance enhancement.

\\end{{document}}"""

        return latex_template

# Tool Functions
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

# LangGraph Agent Functions
def ask_question_node(state: State):
    """Node for asking transparency questions"""
    if state["current_question"] <= 6:
        question = TRANSPARENCY_QUESTIONS[state["current_question"] - 1]
        state["messages"].append({"role": "assistant", "content": question})
    return state

def process_response_node(state: State):
    """Node for processing user responses"""
    if state["current_question"] > 6:
        state["is_complete"] = True
        if state["scores"]:
            state["final_score"] = sum(state["scores"]) / len(state["scores"])
    return state

def should_continue(state: State):
    """Decide whether to continue or end"""
    if state["is_complete"] or state["current_question"] > 6:
        return "end"
    return "continue"

# Create LangGraph workflow
workflow = StateGraph(State)

# Add nodes
workflow.add_node("ask_question", ask_question_node)
workflow.add_node("process_response", process_response_node)

# Add edges
workflow.add_edge(START, "ask_question")
workflow.add_edge("ask_question", "process_response")

# Add conditional edges
workflow.add_conditional_edges(
    "process_response",
    should_continue,
    {
        "continue": "ask_question",
        "end": END
    }
)

# Compile the graph
app_graph = workflow.compile()

# FastAPI App
app = FastAPI(title="Product Transparency Assessment API", version="1.0.0")
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication dependency
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Implement your token verification logic here
    # For demo purposes, accepting any token
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

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