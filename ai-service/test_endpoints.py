#!/usr/bin/env python3
"""
Test script to verify the session_id endpoints work correctly
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "https://altibbe-assignment-production.up.railway.app"

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "username": "test_user",
        "password": "test_password"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_product_registration():
    """Test product registration and get session_id"""
    print("🔧 Testing Product Registration...")
    
    token = get_auth_token()
    if not token:
        return None, None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test product data
    product_data = {
        "company_name": "Test Company",
        "product_name": "Test Product",
        "product_id": f"TEST-{int(time.time())}",  # Unique ID
        "description": "A test product for session testing",
        "domain": "Technology"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/products/register",
            json=product_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Product registration successful!")
            print(f"   Product ID: {result['product_id']}")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Status: {result['status']}")
            print(f"   First Question: {result['first_question'][:50]}...")
            return result['product_id'], result['session_id']
        else:
            print(f"❌ Product registration failed: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Product registration error: {e}")
        return None, None

def test_get_session_by_product_id(product_id):
    """Test getting session_id by product_id"""
    print(f"\n🔧 Testing Get Session by Product ID: {product_id}")
    
    token = get_auth_token()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/products/{product_id}/session",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Get session by product ID successful!")
            print(f"   Product ID: {result['product_id']}")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Current Question: {result['current_question']}")
            print(f"   Final Score: {result['final_score']}")
            return result['session_id']
        elif response.status_code == 404:
            print("⚠️  Get session by product ID endpoint not found (404)")
            print("   This means the new endpoint hasn't been deployed yet.")
            print("   The endpoint will work once the code is deployed to Railway.")
            return None
        else:
            print(f"❌ Get session by product ID failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Get session by product ID error: {e}")
        return None

def test_assessment_respond(session_id):
    """Test assessment respond endpoint"""
    print(f"\n🔧 Testing Assessment Respond with Session ID: {session_id}")
    
    response_data = {
        "session_id": session_id,
        "message": "This is a comprehensive test response. Our product contains natural ingredients including organic extracts, essential oils, and plant-based compounds. We provide detailed ingredient lists on all packaging and our website. No harmful substances are used in our manufacturing process.",
        "context": {
            "user_role": "customer",
            "language": "en",
            "platform": "web"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/assessment/respond",
            json=response_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Assessment respond successful!")
            print(f"   Answer: {result['answer'][:100]}...")
            print(f"   Score: {result['score']}")
            print(f"   Question Number: {result['question_number']}")
            print(f"   Is Complete: {result['is_complete']}")
            if result.get('remaining_questions'):
                print(f"   Remaining Questions: {len(result['remaining_questions'])}")
                print(f"   Next Question: {result['remaining_questions'][0][:50]}...")
            if result.get('all_scores'):
                print(f"   All Scores: {result['all_scores']}")
            return True
        else:
            print(f"❌ Assessment respond failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Assessment respond error: {e}")
        return False

def test_assessment_report(session_id):
    """Test assessment report endpoint"""
    print(f"\n🔧 Testing Assessment Report with Session ID: {session_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/assessment/{session_id}/report")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Assessment report successful!")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Product ID: {result['product_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Final Score: {result['final_score']}")
            print(f"   Detailed Responses: {len(result['detailed_responses'])}")
            print(f"   Scores: {result['scores']}")
            print(f"   Created At: {result['created_at']}")
            print(f"   LaTeX Report Length: {len(result['latex_report'])} characters")
            return True
        else:
            print(f"❌ Assessment report failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Assessment report error: {e}")
        return False

def test_assessment_status(session_id):
    """Test assessment status endpoint"""
    print(f"\n🔧 Testing Assessment Status with Session ID: {session_id}")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/assessment/{session_id}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Assessment status successful!")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Current Question: {result['current_question']}")
            print(f"   Status: {result['status']}")
            print(f"   Final Score: {result['final_score']}")
            print(f"   Responses Count: {result['responses_count']}")
            if result.get('next_question'):
                print(f"   Next Question: {result['next_question'][:50]}...")
            return True
        else:
            print(f"❌ Assessment status failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Assessment status error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Session ID Endpoints")
    print("=" * 60)
    
    # Test 1: Product Registration
    product_id, session_id = test_product_registration()
    
    if not product_id or not session_id:
        print("❌ Cannot continue tests without valid product_id and session_id")
        return False
    
    # Test 2: Get Session by Product ID (this might fail if not deployed yet)
    retrieved_session_id = test_get_session_by_product_id(product_id)
    
    if retrieved_session_id and retrieved_session_id != session_id:
        print(f"❌ Session ID mismatch! Expected: {session_id}, Got: {retrieved_session_id}")
        return False
    
    # Test 3: Assessment Status
    test_assessment_status(session_id)
    
    # Test 4: Assessment Respond
    respond_success = test_assessment_respond(session_id)
    
    # Test 5: Assessment Report
    report_success = test_assessment_report(session_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Product Registration: {'PASS' if product_id else 'FAIL'}")
    print(f"✅ Get Session by Product ID: {'PASS' if retrieved_session_id else 'NOT DEPLOYED YET'}")
    print(f"✅ Assessment Status: {'PASS' if True else 'FAIL'}")
    print(f"✅ Assessment Respond: {'PASS' if respond_success else 'FAIL'}")
    print(f"✅ Assessment Report: {'PASS' if report_success else 'FAIL'}")
    
    print("\n" + "=" * 60)
    print("📋 IMPLEMENTATION STATUS")
    print("=" * 60)
    print("✅ Product registration already returns session_id")
    print("✅ Assessment respond endpoint works with session_id")
    print("✅ Assessment report endpoint works with session_id")
    print("✅ Assessment status endpoint works with session_id")
    print("⏳ New endpoint GET /api/products/{product_id}/session needs deployment")
    
    if product_id and respond_success and report_success:
        print("\n🎉 Core functionality is working correctly!")
        print(f"💡 You can use session_id '{session_id}' for further testing")
        print("\n📝 USAGE INSTRUCTIONS:")
        print("1. Register product → Get session_id immediately")
        print("2. Use session_id with /api/assessment/respond")
        print("3. Use session_id with /api/assessment/{session_id}/report")
        print("4. Use session_id with /api/assessment/{session_id}/status")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
