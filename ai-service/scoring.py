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
        As a CRITICAL EVALUATOR of corporate transparency with expertise in Indian consumer safety regulations, conduct a RIGOROUS assessment of this response using multiple weighted parameters.

        Question {question_number}: {question}
        Response: {response}

        EVALUATION FRAMEWORK - Score each parameter on a 1-7 scale:

        PARAMETER 1: EVIDENCE QUALITY & VERIFICATION (Weight: 20 points)
        Score 1-7 based on:
        - 7: Provides specific certificate numbers, license IDs, test report references with exact dates
        - 6: Includes verifiable documentation with most details present
        - 5: Shows some specific evidence but missing key verification details
        - 4: Mentions certifications but lacks specific reference numbers
        - 3: Vague references to compliance without verifiable evidence
        - 2: Generic claims like "we are certified" without specifics
        - 1: No evidence or completely unverifiable claims

        PARAMETER 2: TRANSPARENCY DEPTH & HONESTY (Weight: 20 points)
        Score 1-7 based on:
        - 7: Explicitly admits knowledge gaps, discusses failures, compares honestly with competitors
        - 6: Shows good transparency with minor limitations in honesty
        - 5: Some acknowledgment of limitations but avoids discussing negative aspects
        - 4: Basic transparency but lacks depth in self-criticism
        - 3: Limited transparency, mostly positive information only
        - 2: Minimal transparency, avoids difficult topics
        - 1: No transparency, only promotional content

        PARAMETER 3: REGULATORY COMPLIANCE & LEGAL PRECISION (Weight: 20 points)
        Score 1-7 based on:
        - 7: Cites exact regulation numbers, sections, dates with current compliance proof
        - 6: Strong regulatory knowledge with specific references
        - 5: Good understanding of regulations with some specific citations
        - 4: Basic regulatory awareness but lacks specific details
        - 3: General mentions of compliance without specifics
        - 2: Vague references to regulations
        - 1: No regulatory knowledge or incorrect information

        PARAMETER 4: DATA SPECIFICITY & ACCURACY (Weight: 15 points)
        Score 1-7 based on:
        - 7: Provides exact numbers, concentrations, dates with precise measurements
        - 6: Highly specific data with minor gaps in precision
        - 5: Good specificity but some round numbers or ranges
        - 4: Moderate specificity with some vague data points
        - 3: Limited specificity, mostly general statements
        - 2: Very vague data with few specific details
        - 1: No specific data or contradictory information

        PARAMETER 5: RESPONSE METHODOLOGY & REASONING (Weight: 15 points)
        Score 1-7 based on:
        - 7: Clear logical progression with step-by-step reasoning and critical analysis
        - 6: Well-structured response with good reasoning
        - 5: Logical flow with some analytical depth
        - 4: Basic structure but limited reasoning depth
        - 3: Disorganized or superficial reasoning
        - 2: Poor structure with minimal reasoning
        - 1: Illogical or no reasoning demonstrated

        PARAMETER 6: CONSUMER SAFETY & ACTIONABILITY (Weight: 10 points)
        Score 1-7 based on:
        - 7: Provides specific safety instructions, risk mitigation, actionable guidance
        - 6: Good safety information with clear instructions
        - 5: Adequate safety information but limited actionability
        - 4: Basic safety mentions without detailed guidance
        - 3: Limited safety information
        - 2: Minimal safety considerations
        - 1: No safety information or misleading guidance

        SCORING INSTRUCTIONS:
        1. Evaluate each parameter independently on 1-7 scale
        2. Be strict - most responses should score 2-4 on each parameter
        3. Only award 6-7 for truly exceptional transparency
        4. Consider both content quality and response methodology

        PENALTY SYSTEM (subtract from total):
        - Marketing language: -5 points
        - Contradictory information: -10 points
        - Missing critical safety info: -15 points
        - Incomplete response (<100 words): -10 points

        Provide your evaluation in this EXACT format:
        Parameter 1: [score 1-7]
        Parameter 2: [score 1-7]
        Parameter 3: [score 1-7]
        Parameter 4: [score 1-7]
        Parameter 5: [score 1-7]
        Parameter 6: [score 1-7]
        Penalties: -[total penalty points]
        """
        
        try:
            completion = groq_client.chat.completions.create(
                model="qwen/qwen3-32b",  # Upgraded to 70B for better reasoning
                messages=[{"role": "user", "content": scoring_prompt}],
                temperature=0.1,  # Very low temperature for consistent analytical reasoning
                max_tokens=200  # Increased for structured parameter scoring
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Parse the structured response
            lines = response_text.split('\n')
            scores = []
            penalties = 0
            
            # Weights for each parameter (total = 100)
            weights = [20, 20, 20, 15, 15, 10]  # Sum = 100
            
            for line in lines:
                line = line.strip()
                if line.startswith('Parameter'):
                    # Extract score from "Parameter X: [score]"
                    parts = line.split(':')
                    if len(parts) == 2:
                        score_text = parts[1].strip()
                        score = int(''.join(filter(str.isdigit, score_text)))
                        scores.append(max(1, min(7, score)))  # Ensure 1-7 range
                elif line.startswith('Penalties'):
                    # Extract penalty points
                    penalty_text = line.split(':')[1].strip() if ':' in line else line
                    penalty_digits = ''.join(filter(str.isdigit, penalty_text))
                    if penalty_digits:
                        penalties = int(penalty_digits)
            
            # Calculate weighted score
            if len(scores) == 6:
                # Calculate weighted average and convert to 0-100 scale
                weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
                max_possible = sum(7 * weight for weight in weights)  # 7 * 100 = 700
                percentage = (weighted_sum / max_possible) * 100
                
                # Apply penalties
                final_score = max(0, percentage - penalties)
                return int(final_score)
            else:
                # Fallback if parsing fails
                return 12
            
        except Exception as e:
            print(f"Error scoring response: {e}")
            return 12  # Default moderate score on error (middle of 0-100 scale)