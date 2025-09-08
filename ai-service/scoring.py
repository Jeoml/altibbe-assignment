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
        As a CRITICAL EVALUATOR of corporate transparency with expertise in Indian consumer safety regulations, conduct a RIGOROUS, UNFORGIVING assessment of this response. Apply EXTREME SCRUTINY - most responses should score 2-3 marks out of 10.

        Question {question_number}: {question}
        Response: {response}

        CRITICAL EVALUATION FRAMEWORK - Apply HARSH STANDARDS:

        1. EVIDENCE QUALITY & VERIFICATION (3 points) - ZERO TOLERANCE FOR WEAK EVIDENCE:
           
           a) DOCUMENTARY PROOF REQUIREMENT (1 point):
              - ONLY award if response provides SPECIFIC, VERIFIABLE documentation
              - Certificate numbers, license IDs, test report references MUST be included
              - Generic statements like "we are certified" = 0 points
              - Missing verifiable evidence = AUTOMATIC 0
           
           b) THIRD-PARTY VERIFICATION (1 point):
              - ONLY award if response mentions INDEPENDENT verification bodies
              - Must specify WHO verified, WHEN, and WHAT standards
              - Self-claims without external validation = 0 points
              - Vague references to "authorities" = 0 points
           
           c) DATA SPECIFICITY & ACCURACY (1 point):
              - ONLY award if response provides EXACT numbers, dates, concentrations
              - Ranges without specific values = 0 points
              - Round numbers without precision = 0 points
              - Any contradictory or inconsistent data = 0 points

        2. TRANSPARENCY DEPTH & HONESTY (3 points) - DEMAND COMPLETE CANDOR:
           
           a) LIMITATION ACKNOWLEDGMENT (1 point):
              - ONLY award if response explicitly states what they DON'T know
              - Must admit specific knowledge gaps or uncertainties
              - Overconfident claims without caveats = 0 points
              - Marketing language without honest limitations = 0 points
           
           b) NEGATIVE ASPECT DISCLOSURE (1 point):
              - ONLY award if response discusses downsides, risks, or failures
              - Must provide specific examples of problems or limitations
              - Only positive information = 0 points
              - Downplaying or hiding negative aspects = 0 points
           
           c) COMPARATIVE HONESTY (1 point):
              - ONLY award if response compares honestly with competitors/alternatives
              - Must acknowledge where others might be better
              - Only self-promotional content = 0 points
              - Unfair competitive comparisons = 0 points

        3. REGULATORY COMPLIANCE & LEGAL PRECISION (2 points) - DEMAND EXACT COMPLIANCE:
           
           a) SPECIFIC REGULATION CITATION (1 point):
              - ONLY award if response cites EXACT regulation numbers, sections, dates
              - Must reference specific BIS standards, FSSAI guidelines, Act sections
              - General mentions of "regulations" = 0 points
              - Incorrect or outdated regulatory references = 0 points
           
           b) COMPLIANCE EVIDENCE (1 point):
              - ONLY award if response provides PROOF of compliance
              - Must show audit results, inspection reports, or enforcement actions
              - Claims without evidence = 0 points
              - Past compliance without current status = 0 points

        4. RESPONSE METHODOLOGY & REASONING (2 points) - EVALUATE HOW THEY ANSWER:
           
           a) LOGICAL STRUCTURE & REASONING (1 point):
              - ONLY award if response follows clear logical progression
              - Must show step-by-step reasoning with premises and conclusions
              - Disorganized or illogical flow = 0 points
              - Jumping to conclusions without reasoning = 0 points
           
           b) CRITICAL ANALYSIS DEPTH (1 point):
              - ONLY award if response demonstrates deep analytical thinking
              - Must show consideration of multiple perspectives and implications
              - Surface-level responses = 0 points
              - No critical evaluation of own claims = 0 points

        AUTOMATIC PENALTY SYSTEM - DEDUCT POINTS FOR:
        - Marketing language or promotional content: -1 point
        - Vague or non-specific statements: -1 point  
        - Contradictory information: -1 point
        - Missing critical safety information: -1 point
        - Incomplete responses (less than 100 words): -1 point
        - No actionable information for consumers: -1 point

        SCORING CALIBRATION - BE EXTREMELY STRICT:
        - 8-10: EXCEPTIONAL (rare) - Perfect evidence, complete honesty, flawless compliance
        - 6-7: GOOD (uncommon) - Strong evidence with minor gaps
        - 4-5: ADEQUATE (occasional) - Basic compliance with significant limitations
        - 2-3: POOR (typical) - Major gaps in evidence, honesty, or compliance
        - 0-1: FAILURE (common) - Inadequate response with critical failures

        CRITICAL EVALUATION RULES:
        1. Start with 0 points and award ONLY for exceptional merit
        2. Apply penalties liberally for any transparency failures
        3. Most responses should score 2-3 due to typical corporate evasiveness
        4. Only award high scores for truly exceptional transparency
        5. Consider the response methodology - HOW they answer matters as much as WHAT they answer

        After this rigorous analysis, provide ONLY the final numerical score (0-10) that reflects the harsh standards applied.
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
            return max(0, min(10, score))  # Ensure score is between 0-10
            
        except Exception as e:
            print(f"Error scoring response: {e}")
            return 5  # Default moderate score on error (middle of 0-10 scale)