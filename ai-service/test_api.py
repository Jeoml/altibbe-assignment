"""
Test script for the Product Transparency Assessment API
"""

import requests
import json
from datetime import datetime

# API base URL (adjust if needed)
BASE_URL = "http://localhost:8000"

# Mock auth token (since we accept any token for demo)
HEADERS = {
    "Authorization": "Bearer test-token",
    "Content-Type": "application/json"
}

def test_product_registration():
    """Test product registration endpoint"""
    print("🧪 Testing Product Registration...")
    
    product_data = {
        "company_name": "TestCorp Ltd",
        "product_name": "TestProduct Pro",
        "product_id": f"test-product-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "description": "A test product for transparency assessment",
        "domain": "Consumer Electronics"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/products/register",
        headers=HEADERS,
        json=product_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Product registered successfully!")
        print(f"📝 Session ID: {result['session_id']}")
        print(f"🔍 First Question: {result['first_question']}")
        print(f"📋 Remaining Questions Count: {len(result.get('remaining_questions', []))}")
        return result['session_id']
    else:
        print(f"❌ Registration failed: {response.text}")
        return None

def test_first_response(session_id):
    """Test responding to the first question"""
    print("\n🧪 Testing First Response...")
    
    response_data = {
        "session_id": session_id,
        "message": "Our product contains high-quality organic ingredients including natural oils, plant extracts, and essential vitamins. We maintain complete transparency about all components and their sources. All ingredients are ethically sourced and undergo rigorous testing for purity and safety."
    }
    
    response = requests.post(
        f"{BASE_URL}/api/assessment/respond",
        headers=HEADERS,
        json=response_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ First response processed successfully!")
        print(f"📊 Score for Question 1: {result['score']}")
        print(f"🔍 Remaining Questions Count: {len(result.get('remaining_questions', []))}")
        print(f"✅ Is Complete: {result['is_complete']}")
        
        if result.get('remaining_questions'):
            print("\n📋 Remaining Questions:")
            for i, question in enumerate(result['remaining_questions'], 2):
                print(f"  {i}. {question}")
        
        return result
    else:
        print(f"❌ Response failed: {response.text}")
        return None

def test_multiple_responses(session_id):
    """Test responding to multiple questions at once"""
    print("\n🧪 Testing Multiple Responses...")
    
    # Sample responses for questions 2-6
    sample_responses = [
        "We implement ISO 9001 quality management standards with third-party certifications from SGS and Bureau Veritas. Our manufacturing follows GMP guidelines with regular audits and batch testing for every production run.",
        
        "Our product is generally safe for most users, but we clearly label potential allergens. Pregnant women and individuals with specific medical conditions should consult healthcare providers. We provide comprehensive usage guidelines on all packaging.",
        
        "We use biodegradable packaging and renewable energy in 70% of our production. Our carbon footprint is offset through verified environmental programs. Disposal instructions are clearly marked on packaging for responsible waste management.",
        
        "Product shelf life is 24 months when stored in cool, dry conditions below 25°C. We provide clear expiration dates, storage guidelines, and usage instructions in multiple languages on all packaging materials.",
        
        "We maintain a 24/7 customer service system for complaints and adverse event reporting. All incidents are tracked in our database and reported to regulatory authorities within 24 hours. We have a transparent recall process with public notifications."
    ]
    
    response_data = {
        "session_id": session_id,
        "responses": sample_responses
    }
    
    response = requests.post(
        f"{BASE_URL}/api/assessment/respond-multiple",
        headers=HEADERS,
        json=response_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Multiple responses processed successfully!")
        print(f"🎯 Final Assessment Complete: {result['is_complete']}")
        print(f"📊 Final Score: {result.get('final_score', 'N/A')}")
        print(f"📈 All Scores: {result.get('all_scores', [])}")
        print(f"✅ Questions Answered: {result.get('total_questions_answered', 0)}")
        
        return result
    else:
        print(f"❌ Multiple responses failed: {response.text}")
        return None

def test_assessment_report(session_id):
    """Test getting the final assessment report"""
    print("\n🧪 Testing Assessment Report...")
    
    response = requests.get(
        f"{BASE_URL}/api/assessment/{session_id}/report",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Assessment report retrieved successfully!")
        print(f"📊 Final Score: {result['final_score']}")
        print(f"📋 Status: {result['status']}")
        print(f"🔢 Total Responses: {len(result.get('detailed_responses', []))}")
        
        return result
    else:
        print(f"❌ Report retrieval failed: {response.text}")
        return None

def main():
    """Run all tests"""
    print("🚀 Starting API Tests...\n")
    
    # Test 1: Register product
    session_id = test_product_registration()
    if not session_id:
        print("❌ Cannot continue without session ID")
        return
    
    # Test 2: Submit first response and get remaining questions
    first_result = test_first_response(session_id)
    if not first_result:
        print("❌ Cannot continue without first response")
        return
    
    # Test 3: Submit multiple responses for remaining questions
    multiple_result = test_multiple_responses(session_id)
    if not multiple_result:
        print("❌ Multiple responses failed")
        return
    
    # Test 4: Get final assessment report
    report_result = test_assessment_report(session_id)
    
    print("\n🎉 All tests completed!")
    print(f"📊 Final Transparency Score: {multiple_result.get('final_score', 'N/A')}")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
