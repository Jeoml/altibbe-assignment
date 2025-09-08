#!/usr/bin/env python3
"""
Demonstration script showing how to use the session_id functionality
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://altibbe-assignment-production.up.railway.app"

def get_auth_token():
    """Get authentication token"""
    login_data = {"username": "test_user", "password": "test_password"}
    response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    return response.json()["access_token"] if response.status_code == 200 else None

def demo_complete_workflow():
    """Demonstrate the complete workflow using session_id"""
    print("🚀 DEMO: Complete Session ID Workflow")
    print("=" * 50)
    
    # Step 1: Register Product and Get Session ID
    print("\n1️⃣ REGISTERING PRODUCT...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    product_data = {
        "company_name": "Demo Company",
        "product_name": "Demo Product",
        "product_id": f"DEMO-{int(time.time())}",
        "description": "A demonstration product",
        "domain": "Technology"
    }
    
    response = requests.post(f"{BASE_URL}/api/products/register", json=product_data, headers=headers)
    result = response.json()
    
    session_id = result['session_id']
    product_id = result['product_id']
    
    print(f"✅ Product registered: {product_id}")
    print(f"✅ Session ID obtained: {session_id}")
    
    # Step 2: Submit Assessment Responses
    print(f"\n2️⃣ SUBMITTING ASSESSMENT RESPONSES...")
    
    responses = [
        "Our product contains natural ingredients including organic extracts, essential oils, and plant-based compounds. We provide detailed ingredient lists on all packaging and our website. No harmful substances are used in our manufacturing process.",
        "We have comprehensive quality control measures including ISO 9001 certification, regular third-party testing, and batch tracking. All products undergo rigorous testing for purity, potency, and safety before release.",
        "Our product has a 2-year shelf life when stored in cool, dry conditions. We provide clear usage instructions on packaging and our website. We ensure consumers receive accurate information through multiple channels.",
        "We follow sustainable practices including using recyclable packaging, sourcing from certified suppliers, and implementing waste reduction programs. Our environmental impact is minimal and we provide disposal guidance.",
        "We have a comprehensive system for tracking adverse events and consumer complaints. We maintain transparency about product issues and provide clear resolution processes. All recalls are handled promptly and communicated effectively.",
        "We have robust data protection measures in place. Consumer data is encrypted and stored securely. We comply with all relevant privacy regulations and provide clear privacy policies to our customers."
    ]
    
    for i, response_text in enumerate(responses, 1):
        response_data = {
            "session_id": session_id,
            "message": response_text,
            "context": {"user_role": "customer", "language": "en", "platform": "web"}
        }
        
        response = requests.post(f"{BASE_URL}/api/assessment/respond", json=response_data)
        result = response.json()
        
        print(f"   Question {i}: Score {result['score']} - {'Complete!' if result['is_complete'] else 'Continue...'}")
        
        if result['is_complete']:
            print(f"   🎉 Final Score: {result['final_score']}")
            break
    
    # Step 3: Get Assessment Report
    print(f"\n3️⃣ GENERATING ASSESSMENT REPORT...")
    
    response = requests.get(f"{BASE_URL}/api/assessment/{session_id}/report")
    report = response.json()
    
    print(f"✅ Report generated successfully!")
    print(f"   Product ID: {report['product_id']}")
    print(f"   Final Score: {report['final_score']}")
    print(f"   Total Responses: {len(report['detailed_responses'])}")
    print(f"   Report Length: {len(report['latex_report'])} characters")
    
    # Step 4: Get Assessment Status
    print(f"\n4️⃣ CHECKING ASSESSMENT STATUS...")
    
    response = requests.get(f"{BASE_URL}/api/assessment/{session_id}/status", headers=headers)
    status = response.json()
    
    print(f"✅ Status retrieved successfully!")
    print(f"   Status: {status['status']}")
    print(f"   Current Question: {status['current_question']}")
    print(f"   Responses Count: {status['responses_count']}")
    
    print(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
    print(f"💡 Session ID '{session_id}' can be used for all assessment operations")
    
    return session_id, product_id

def demo_api_examples():
    """Show API usage examples"""
    print("\n" + "=" * 50)
    print("📚 API USAGE EXAMPLES")
    print("=" * 50)
    
    print("\n🔐 1. Authentication:")
    print("POST /api/auth/login")
    print("Body: {username: 'user', password: 'pass'}")
    
    print("\n📝 2. Register Product (Gets session_id):")
    print("POST /api/products/register")
    print("Headers: {Authorization: 'Bearer <token>'}")
    print("Body: {company_name, product_name, product_id, description, domain}")
    print("Response: {session_id, product_id, first_question, ...}")
    
    print("\n💬 3. Submit Response:")
    print("POST /api/assessment/respond")
    print("Body: {session_id, message, context}")
    print("Response: {answer, score, question_number, remaining_questions, ...}")
    
    print("\n📊 4. Get Report:")
    print("GET /api/assessment/{session_id}/report")
    print("Response: {session_id, product_id, final_score, detailed_responses, latex_report, ...}")
    
    print("\n📈 5. Get Status:")
    print("GET /api/assessment/{session_id}/status")
    print("Headers: {Authorization: 'Bearer <token>'}")
    print("Response: {session_id, current_question, status, final_score, ...}")
    
    print("\n🔍 6. Get Session by Product ID (After Deployment):")
    print("GET /api/products/{product_id}/session")
    print("Headers: {Authorization: 'Bearer <token>'}")
    print("Response: {product_id, session_id, status, current_question, ...}")

if __name__ == "__main__":
    try:
        session_id, product_id = demo_complete_workflow()
        demo_api_examples()
        
        print(f"\n✨ SUMMARY:")
        print(f"   Product ID: {product_id}")
        print(f"   Session ID: {session_id}")
        print(f"   All endpoints working correctly!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
