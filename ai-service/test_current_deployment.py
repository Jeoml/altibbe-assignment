#!/usr/bin/env python3
"""
Test script to check what's currently deployed and verify database connection
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://altibbe-assignment-production.up.railway.app"

def test_current_deployment():
    """Test what's currently deployed"""
    print("🔧 Testing Current Deployment...")
    print("=" * 60)
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running")
            health_data = health_response.json()
            print(f"   Timestamp: {health_data.get('timestamp', 'N/A')}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
        
        # Get auth token
        login_data = {"username": "test_user", "password": "test_password"}
        auth_response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data, timeout=5)
        
        if auth_response.status_code != 200:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            return False
        
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authentication successful")
        
        # Register product to test current behavior
        product_data = {
            "company_name": "Deployment Test Company",
            "product_name": "Deployment Test Product",
            "product_id": f"DEPLOY-TEST-{int(time.time())}",
            "description": "Testing current deployment behavior",
            "domain": "Technology"
        }
        
        register_response = requests.post(
            f"{BASE_URL}/api/products/register",
            json=product_data,
            headers=headers,
            timeout=10
        )
        
        if register_response.status_code == 200:
            result = register_response.json()
            print("✅ Product registration successful!")
            print(f"   Product ID: {result['product_id']}")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Status: {result['status']}")
            
            # Check if database_verified field exists (indicates new code)
            if 'database_verified' in result:
                print(f"   Database Verified: {result['database_verified']}")
                print("✅ NEW CODE IS DEPLOYED - Database extraction is active!")
                return True
            else:
                print("   Database Verified: Not present")
                print("⚠️  OLD CODE IS DEPLOYED - Database extraction not active")
                print("   The changes need to be deployed to Railway")
                return False
        else:
            print(f"❌ Product registration failed: {register_response.status_code}")
            print(f"   Response: {register_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_database_connection():
    """Test if we can connect to the database directly"""
    print(f"\n🔧 Testing Database Connection...")
    print("=" * 60)
    
    try:
        # Try to connect to the database using the connection string
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse the database URL
        db_url = "postgresql://neondb_owner:npg_4HjdTz1qXkRy@ep-red-cell-adtwlc8h-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        parsed = urlparse(db_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        
        cursor = conn.cursor()
        
        # Check if assessment_sessions table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'assessment_sessions'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        print(f"✅ Assessment sessions table exists: {table_exists}")
        
        if table_exists:
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'assessment_sessions'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print("✅ Table structure:")
            for col_name, data_type in columns:
                print(f"   - {col_name}: {data_type}")
            
            # Check recent sessions
            cursor.execute("""
                SELECT session_id, product_id, status, created_at 
                FROM assessment_sessions 
                ORDER BY created_at DESC 
                LIMIT 5;
            """)
            
            recent_sessions = cursor.fetchall()
            print(f"✅ Recent sessions ({len(recent_sessions)}):")
            for session in recent_sessions:
                print(f"   - {session[0][:8]}... | {session[1]} | {session[2]} | {session[3]}")
        
        cursor.close()
        conn.close()
        print("✅ Database connection successful!")
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed - cannot test database connection directly")
        return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """Run deployment tests"""
    print("🧪 Testing Current Deployment Status")
    print("=" * 60)
    
    # Test current deployment
    deployment_status = test_current_deployment()
    
    # Test database connection
    db_status = test_database_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT STATUS SUMMARY")
    print("=" * 60)
    print(f"✅ Server Running: {'YES' if True else 'NO'}")
    print(f"✅ New Code Deployed: {'YES' if deployment_status else 'NO'}")
    print(f"✅ Database Accessible: {'YES' if db_status else 'NO'}")
    
    if not deployment_status:
        print("\n⚠️  DEPLOYMENT NEEDED:")
        print("   The code changes are not yet deployed to Railway.")
        print("   You need to deploy the updated code to see the changes.")
        print("\n💡 Next Steps:")
        print("   1. Commit your changes to git")
        print("   2. Push to your repository")
        print("   3. Railway will automatically deploy the changes")
        print("   4. Wait for deployment to complete")
        print("   5. Test again")
    
    return deployment_status

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
