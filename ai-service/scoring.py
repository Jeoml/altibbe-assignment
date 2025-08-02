"""
Scoring system for transparency responses
"""

from groq import Groq
from config import GROQ_API_KEY

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

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