#!/usr/bin/env python3
"""
Test script to demonstrate how to get prediction history for authenticated user
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/login"
HISTORY_URL = f"{BASE_URL}/history"

def test_user_login_and_history():
    """Test user login and fetch prediction history"""
    
    # Step 1: Login to get JWT token
    print("🔐 Step 1: Logging in user...")
    login_data = {
        "email": "test@example.com",  # Replace with your test user email
        "password": "password123"      # Replace with your test user password
    }
    
    try:
        login_response = requests.post(LOGIN_URL, json=login_data)
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            jwt_token = login_result.get('access_token')
            print(f"✅ Login successful! JWT Token: {jwt_token[:50]}...")
            
            # Step 2: Get user's prediction history
            print("\n📊 Step 2: Fetching prediction history...")
            
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            }
            
            # Get first page of history
            history_response = requests.get(HISTORY_URL, headers=headers)
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                print("✅ History retrieved successfully!")
                print(f"📈 Total predictions: {history_data['pagination']['total']}")
                
                if history_data['history']:
                    print("\n🌻 Recent Predictions:")
                    for i, analysis in enumerate(history_data['history'][:3], 1):  # Show first 3
                        print(f"\n  {i}. Analysis ID: {analysis['id']}")
                        print(f"     Predicted: {analysis['predicted_class']}")
                        print(f"     Confidence: {analysis['confidence']:.2%}")
                        print(f"     Image: {analysis['image_info']['filename']}")
                        print(f"     Date: {analysis['created_at']}")
                        if analysis['images']['original_image_url']:
                            print(f"     Image URL: {analysis['images']['original_image_url']}")
                else:
                    print("📭 No prediction history found for this user")
                
                # Step 3: Test pagination (get page 2 if exists)
                if history_data['pagination']['has_next']:
                    print(f"\n📄 Step 3: Getting page 2...")
                    page2_response = requests.get(f"{HISTORY_URL}?page=2", headers=headers)
                    if page2_response.status_code == 200:
                        page2_data = page2_response.json()
                        print(f"✅ Page 2 has {len(page2_data['history'])} more predictions")
                
                # Step 4: Test getting specific analysis
                if history_data['history']:
                    first_analysis_id = history_data['history'][0]['id']
                    print(f"\n🔍 Step 4: Getting specific analysis {first_analysis_id}...")
                    
                    specific_url = f"{BASE_URL}/history/{first_analysis_id}"
                    specific_response = requests.get(specific_url, headers=headers)
                    
                    if specific_response.status_code == 200:
                        specific_data = specific_response.json()
                        analysis = specific_data['analysis']
                        print("✅ Specific analysis retrieved!")
                        print(f"   All predictions: {json.dumps(analysis['all_predictions'], indent=2)}")
                    else:
                        print(f"❌ Failed to get specific analysis: {specific_response.text}")
                
            else:
                print(f"❌ Failed to get history: {history_response.status_code}")
                print(f"Response: {history_response.text}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error! Make sure your server is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_curl_examples():
    """Show curl command examples"""
    print("\n" + "="*60)
    print("📋 CURL COMMAND EXAMPLES")
    print("="*60)
    
    print("\n1. Login to get JWT token:")
    print('curl -X POST "http://localhost:5000/login" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"email": "test@example.com", "password": "password123"}\'')
    
    print("\n2. Get prediction history (replace YOUR_JWT_TOKEN):")
    print('curl -X GET "http://localhost:5000/history" \\')
    print('  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\')
    print('  -H "Content-Type: application/json"')
    
    print("\n3. Get paginated history:")
    print('curl -X GET "http://localhost:5000/history?page=1&per_page=5" \\')
    print('  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\')
    print('  -H "Content-Type: application/json"')
    
    print("\n4. Get specific analysis by ID:")
    print('curl -X GET "http://localhost:5000/history/1" \\')
    print('  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\')
    print('  -H "Content-Type: application/json"')

if __name__ == "__main__":
    print("🌻 Sunflower Backend - History Endpoint Test")
    print("="*50)
    
    # Show curl examples first
    show_curl_examples()
    
    print("\n" + "="*60)
    print("🧪 AUTOMATED TEST")
    print("="*60)
    
    # Run automated test
    test_user_login_and_history()
    
    print("\n" + "="*60)
    print("✅ Test completed!")
    print("💡 Use the curl commands above to test manually")
    print("="*60)
