"""
HTML report generation for transparency assessments
"""

import json
from datetime import datetime
from typing import Dict, List
from groq import Groq
from config import GROQ_API_KEY, TRANSPARENCY_QUESTIONS

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

class HtmlReportGenerator:
    @staticmethod
    def generate_transparency_report(
        product_data: Dict,
        session_data: Dict,
        responses: List[Dict],
        scores: List[int],
        final_score: float
    ) -> str:
        """Generate a comprehensive HTML transparency report using LLM"""
        
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
        As a professional regulatory compliance expert and technical writer, generate a comprehensive HTML transparency assessment report based on the following product assessment data:

        ASSESSMENT DATA:
        {json.dumps(assessment_data, indent=2, default=str)}

        REPORT REQUIREMENTS:

        1. DOCUMENT STRUCTURE:
           - Stick to one color which is Deep Blue in little details.
           - Use a clean and professional layout
           - Generate content which fits in A4 paper size sheets perfectly
           - Professional HTML document with embedded CSS
           - Modern, responsive design
           - Clear sections with proper HTML5 semantic structure
           - Include header, main content sections, and footer
           - Professional styling with CSS

        2. CONTENT SECTIONS TO INCLUDE:
           a) Header with product details and assessment metadata
           b) Executive Summary (key findings and overall transparency score)
           c) Assessment Methodology overview
           d) Detailed Analysis for each transparency dimension:
              - Ingredient/Component Transparency
              - Quality Control & Certifications
              - Risk Communication & Safety
              - Environmental Impact & Sustainability
              - Product Information & Usage Guidelines
              - Complaint Management & Recall Systems
           e) Scoring Analysis with visual elements (tables, progress bars)
           f) Regulatory Compliance Assessment
           g) Recommendations for Improvement
           h) Conclusion

        3. STYLING REQUIREMENTS:
           - Modern CSS with professional color scheme
           - Responsive design that works on desktop and mobile
           - Clean typography with good readability
           - Professional tables with proper styling
           - Progress bars or visual indicators for scores
           - Print-friendly styles
           - Bootstrap-like grid system or flexbox layouts
           - Complete responsive design for all screen sizes
           - All typography, spacing, and layout styles
           - Complete table styling with professional appearance
           - Full progress bar/score visualization CSS
           - Complete print media styles
           - All hover effects and interactive elements

        4. CONTENT GENERATION REQUIREMENTS:
           - Analyze the actual assessment data provided
           - Generate specific insights based on the responses
           - Create detailed findings for each question and score
           - Provide regulatory compliance analysis based on Indian standards
           - Generate actionable recommendations based on assessment gaps
           - Create professional executive summary reflecting actual results

        5. TECHNICAL COMPLETENESS:
           - Valid, complete HTML5 structure
           - All CSS embedded and functional
           - Complete semantic markup
           - Full accessibility implementation
           - Complete meta information

        Generate the COMPLETE HTML document. Do not use any templates, placeholders, or incomplete sections. The output must be a fully functional, comprehensive transparency assessment report that can be immediately saved and used. Start with <!DOCTYPE html> and end with </html> with everything in between fully implemented.
        """
        
        try:
            completion = groq_client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[{"role": "user", "content": report_generation_prompt}],
                temperature=0.1,  # Very low temperature for consistent output
                max_tokens=8000  # Increased for comprehensive report
            )
            
            html_report = completion.choices[0].message.content.strip()
            
            # Clean up the HTML code if needed
            if not html_report.startswith("<!DOCTYPE html>"):
                # Extract HTML code if wrapped in markdown
                if "```html" in html_report:
                    start = html_report.find("```html") + 7
                    end = html_report.rfind("```")
                    if end > start:
                        html_report = html_report[start:end].strip()
                elif "```" in html_report:
                    start = html_report.find("```") + 3
                    end = html_report.rfind("```")
                    if end > start:
                        html_report = html_report[start:end].strip()
            
            # Validate that we have a complete HTML document
            if not html_report.startswith("<!DOCTYPE html>") or not html_report.endswith("</html>"):
                raise Exception("Generated report is not a complete HTML document")
            
            return html_report
            
        except Exception as e:
            print(f"Error generating HTML report: {e}")
            # Return error message instead of incomplete template
            return f"""<!DOCTYPE html>
<html>
<head>
    <title>Report Generation Error</title>
</head>
<body>
    <h1>Error Generating Report</h1>
    <p>Unable to generate transparency report: {str(e)}</p>
    <p>Please try again or contact support.</p>
</body>
</html>"""